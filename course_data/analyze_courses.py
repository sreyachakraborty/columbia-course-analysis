import json
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Step 1: Load data
with open("spring_2026_course_reviews.json", "r") as f:
    data = json.load(f)

# Step 2: Keyword labeling (removed 'hard' and 'challenging' - too ambiguous)
HARD = [
    'brutal', 'insane', 'killer', 'impossible', 'tough', 'intense', 
    'difficult', 'heavy', 'crazy', 'nightmare', 'death',
    'destroyed', 'struggled', 'overwhelming', 'exhausting', 'grueling',
    'no sleep', 'all-nighter', 'stressful', 'demanding', 'rigorous',
    'rough', 'painful', 'suffer', 'hell', 'hard', 'challenging'
]

EASY = [
    'easy', 'manageable', 'light', 'chill', 'straightforward', 
    'fair', 'doable', 'simple', 'reasonable',
    'relaxed', 'enjoyable', 'not bad', 'breeze', 'smooth',
    'beginner-friendly', 'gentle', 'accessible', 'easiest'
]

def keyword_label(text):
    text = text.lower()
    hard = sum(1 for w in HARD if w in text)
    easy = sum(1 for w in EASY if w in text)
    if hard > easy:
        return 'hard'
    elif easy > hard:
        return 'easy'
    return 'medium'

def get_review_text(review):
    """Combine content and workload for full context"""
    content = review.get('content', '') or ''
    workload = review.get('workload', '') or ''
    return (content + " " + workload).strip()

def get_time_weight(date_str, decay_years=5):
    """
    More recent reviews get higher weight.
    Reviews from today = 1.0
    Reviews from decay_years ago = 0.3
    """
    if not date_str:
        return 0.5
    
    try:
        review_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        days_ago = (datetime.now() - review_date.replace(tzinfo=None)).days
        years_ago = days_ago / 365
        
        if years_ago <= 0:
            return 1.0
        elif years_ago >= decay_years:
            return 0.3
        else:
            return 1.0 - (years_ago / decay_years) * 0.7
    except:
        return 0.5

# Step 3: Collect all review texts for training
all_texts = []
all_labels = []

for course in data:
    for review in course.get('reviews', []):
        full_text = get_review_text(review)
        if full_text and len(full_text) > 20:
            all_texts.append(full_text)
            all_labels.append(keyword_label(full_text))

print(f"Training on {len(all_texts)} review texts (content + workload)")
print(f"Distribution: {all_labels.count('hard')} hard, {all_labels.count('medium')} medium, {all_labels.count('easy')} easy\n")

# Step 4: Train model
vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
X = vectorizer.fit_transform(all_texts)

model = LogisticRegression(max_iter=1000)
model.fit(X, all_labels)

# Step 5: Helper functions
def get_weighted_difficulty_score(reviews):
    """Get difficulty score weighted by review recency"""
    if not reviews:
        return None, None, []
    
    texts = []
    weights = []
    
    for review in reviews:
        full_text = get_review_text(review)
        if full_text and len(full_text) > 20:
            texts.append(full_text)
            weights.append(get_time_weight(review.get('submission_date')))
    
    if not texts:
        return None, None, []
    
    # Get predictions
    X = vectorizer.transform(texts)
    predictions = model.predict(X)
    
    # Convert to scores
    label_to_score = {'easy': 0, 'medium': 1, 'hard': 2}
    scores = [label_to_score[p] for p in predictions]
    
    # Weighted average
    weighted_sum = sum(s * w for s, w in zip(scores, weights))
    total_weight = sum(weights)
    weighted_avg = weighted_sum / total_weight if total_weight > 0 else None
    
    # Hard percentage (also weighted)
    hard_weighted = sum(w for s, w in zip(scores, weights) if s == 2)
    hard_pct = (hard_weighted / total_weight * 100) if total_weight > 0 else None
    
    return weighted_avg, hard_pct, scores

def get_weighted_rating(reviews):
    """Get rating weighted by review recency"""
    ratings = []
    weights = []
    
    for review in reviews:
        r = review.get('rating')
        if r:
            ratings.append(r)
            weights.append(get_time_weight(review.get('submission_date')))
    
    if not ratings:
        return None, None
    
    # Weighted average
    weighted_sum = sum(r * w for r, w in zip(ratings, weights))
    total_weight = sum(weights)
    weighted_avg = weighted_sum / total_weight if total_weight > 0 else None
    
    # Regular average for comparison
    raw_avg = sum(ratings) / len(ratings)
    
    return weighted_avg, raw_avg

def bayesian_average(value, n, C, m):
    """Bayesian average - accounts for sample size"""
    if value is None:
        return None
    return (n * value + C * m) / (n + C)

# Step 6: Calculate global means
all_ratings = []
for prof in data:
    for review in prof.get('reviews', []):
        r = review.get('rating')
        if r:
            all_ratings.append(r)

global_mean_rating = sum(all_ratings) / len(all_ratings)
global_mean_difficulty = 1.0  # Medium

# Tuning parameters
C_RATING = 20
C_DIFFICULTY = 10
MIN_REVIEWS_RATING = 10
MIN_REVIEWS_DIFFICULTY = 7

print(f"Global mean rating: {global_mean_rating:.2f}")
print(f"Global mean difficulty: {global_mean_difficulty:.2f}")
print(f"C_RATING={C_RATING}, C_DIFFICULTY={C_DIFFICULTY}")
print(f"MIN_REVIEWS_RATING={MIN_REVIEWS_RATING}, MIN_REVIEWS_DIFFICULTY={MIN_REVIEWS_DIFFICULTY}\n")

# Step 7: Rank all professors (with time weighting)
course_rankings = []

for course_entry in data:
    course = course_entry['course']
    reviews = course_entry.get('reviews', [])
    
    # Count reviews with text
    text_count = len([r for r in reviews if len(get_review_text(r)) > 20])
    
    # Get weighted difficulty
    weighted_difficulty, hard_pct, scores = get_weighted_difficulty_score(reviews)
    bayesian_difficulty = bayesian_average(
        weighted_difficulty,
        text_count,
        C_DIFFICULTY, 
        global_mean_difficulty
    )
    
    # Get weighted rating
    weighted_rating, raw_rating = get_weighted_rating(reviews)
    bayesian_rating = bayesian_average(
        weighted_rating,
        len(reviews),
        C_RATING,
        global_mean_rating
    )
    
    course_rankings.append({
        'name': course['name'],
        'course_id': course['course_id'],
        'raw_rating': round(raw_rating, 2) if raw_rating else None,
        'weighted_rating': round(weighted_rating, 2) if weighted_rating else None,
        'bayesian_rating': round(bayesian_rating, 2) if bayesian_rating else None,
        'raw_difficulty': round(sum(scores)/len(scores), 2) if scores else None,
        'weighted_difficulty': round(weighted_difficulty, 2) if weighted_difficulty else None,
        'bayesian_difficulty': round(bayesian_difficulty, 2) if bayesian_difficulty else None,
        'hard_pct': round(hard_pct, 1) if hard_pct else None,
        'review_count': len(reviews),
        'text_count': text_count
    })

# Step 8: Print rankings

# Filter for reliable difficulty data (lower threshold)
reliable_difficulty = [c for c in course_rankings 
                       if c['bayesian_difficulty'] is not None 
                       and c['text_count'] >= MIN_REVIEWS_DIFFICULTY]

# Filter for reliable rating data (higher threshold)
reliable_rating = [c for c in course_rankings 
                   if c['bayesian_rating'] is not None
                   and c['review_count'] >= MIN_REVIEWS_RATING]

print("=" * 110)
print(f"🔥 HARDEST CLASSES (min {MIN_REVIEWS_DIFFICULTY} reviews, time-weighted)")
print("=" * 110)
hardest = sorted(reliable_difficulty, key=lambda x: x['bayesian_difficulty'], reverse=True)[:15]
for i, p in enumerate(hardest, 1):
    hard_pct = p['hard_pct'] if p['hard_pct'] is not None else 0
    raw_diff = p['raw_difficulty'] if p['raw_difficulty'] is not None else 0
    weighted_diff = p['weighted_difficulty'] if p['weighted_difficulty'] is not None else 0
    print(f"{i:2}. {p['name']:<25} Bayesian: {p['bayesian_difficulty']:.2f}  |  Weighted: {weighted_diff:.2f}  |  Raw: {raw_diff:.2f}  |  {hard_pct:.0f}% hard  |  {p['text_count']} reviews")

print("\n" + "=" * 110)
print(f"😌 EASIEST CLASSES (min {MIN_REVIEWS_DIFFICULTY} reviews, time-weighted)")
print("=" * 110)
easiest = sorted(reliable_difficulty, key=lambda x: x['bayesian_difficulty'])[:15]
for i, p in enumerate(easiest, 1):
    hard_pct = p['hard_pct'] if p['hard_pct'] is not None else 0
    raw_diff = p['raw_difficulty'] if p['raw_difficulty'] is not None else 0
    weighted_diff = p['weighted_difficulty'] if p['weighted_difficulty'] is not None else 0
    print(f"{i:2}. {p['name']:<25} Bayesian: {p['bayesian_difficulty']:.2f}  |  Weighted: {weighted_diff:.2f}  |  Raw: {raw_diff:.2f}  |  {hard_pct:.0f}% hard  |  {p['text_count']} reviews")

print("\n" + "=" * 110)
print(f"⭐ BEST RATED CLASSES (min {MIN_REVIEWS_RATING} reviews, Bayesian, time-weighted)")
print("=" * 110)
best_rated = sorted(reliable_rating, key=lambda x: x['bayesian_rating'], reverse=True)[:15]
for i, p in enumerate(best_rated, 1):
    diff = f"{p['bayesian_difficulty']:.2f}" if p['bayesian_difficulty'] is not None else "N/A"
    raw = p['raw_rating'] if p['raw_rating'] is not None else 0
    weighted = p['weighted_rating'] if p['weighted_rating'] is not None else 0
    print(f"{i:2}. {p['name']:<25} Bayesian: {p['bayesian_rating']:.2f}  |  Weighted: {weighted:.2f}  |  Raw: {raw:.2f}  |  Difficulty: {diff}  |  {p['review_count']} reviews")

print("\n" + "=" * 110)
print(f"👎 WORST RATED CLASSES (min {MIN_REVIEWS_RATING} reviews, Bayesian, time-weighted)")
print("=" * 110)
worst_rated = sorted(reliable_rating, key=lambda x: x['bayesian_rating'])[:15]
for i, p in enumerate(worst_rated, 1):
    diff = f"{p['bayesian_difficulty']:.2f}" if p['bayesian_difficulty'] is not None else "N/A"
    raw = p['raw_rating'] if p['raw_rating'] is not None else 0
    weighted = p['weighted_rating'] if p['weighted_rating'] is not None else 0
    print(f"{i:2}. {p['name']:<25} Bayesian: {p['bayesian_rating']:.2f}  |  Weighted: {weighted:.2f}  |  Raw: {raw:.2f}  |  Difficulty: {diff}  |  {p['review_count']} reviews")

# Step 9: Save rankings
with open("course_rankings.json", "w") as f:
    json.dump(course_rankings, f, indent=4)

print(f"\n✅ Saved {len(course_rankings)} course rankings to course_rankings.json")
print(f"   Courses with reliable difficulty data (>={MIN_REVIEWS_DIFFICULTY} reviews): {len(reliable_difficulty)}")
print(f"   Courses with reliable rating data (>={MIN_REVIEWS_RATING} reviews): {len(reliable_rating)}")