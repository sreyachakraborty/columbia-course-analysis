'''
Some courses were either just listed wrong or not in culpa
so here i manually figured out the course IDs for those courses
and then appended the info to the cs_course_reviews.json file
'''

'''
Add missing courses to cs_course_reviews.json by their CULPA course IDs
'''

'''
Add missing courses to cs_course_reviews.json by their CULPA course IDs
'''
'''
Add missing courses to cs_course_reviews.json by their CULPA course IDs
'''

import requests
import json
import time

# Courses with CULPA IDs (found manually)
MISSING_COURSES = [
    (8756, "COMS E6184", "Anonymity & Privacy"),
    (8771, "CSEE E6868", "Embedded Scalable Platforms"),
    (4251, "CSEE W3827", "Fundamentals of Computer Systems"),
    (8774, "CSEE W4121", "Computer Systems for Data Science"),
    (8778, "COMS W4721", "Machine Learning for Data Science"),
    (8773, "CSEE W4840", "Embedded Systems"),
    (7177, "COMS W4232", "Advanced Algorithms")
]

def scrape_course_reviews(course_id, expected_code, expected_name):
    """Scrape all reviews for a single course"""
    all_reviews = []
    seen_ids = set()
    course_info = None
    
    url = f"https://culpa.info/api/review/course/{course_id}"
    params = {'page': 1, 'sort_key': 'null', 'professor_filter': 'null'}
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        return None, []
    
    data = response.json()
    
    # Get course info if available
    course_info = data.get('course')
    
    # If no course info (0 reviews case), create it manually
    if not course_info:
        course_info = {
            'course_id': course_id,
            'course_code': expected_code,
            'name': expected_name,
            'department_id': 7,  # CS department
            'status': 'approved'
        }
        print(f"      No course info returned, using expected: {expected_code}")
    
    reviews = data.get('reviews', [])
    
    # Get all reviews (paginate)
    page = 1
    while reviews:
        for review in reviews:
            review_id = review.get('review_id')
            if review_id and review_id not in seen_ids:
                all_reviews.append(review)
                seen_ids.add(review_id)
        
        page += 1
        time.sleep(0.3)
        response = requests.get(url, params={'page': page, 'sort_key': 'null', 'professor_filter': 'null'})
        
        if response.status_code != 200:
            break
        
        data = response.json()
        reviews = data.get('reviews', [])
    
    return course_info, all_reviews

def add_missing_courses():
    # Load existing data
    with open("cs_course_reviews.json", "r") as f:
        all_courses = json.load(f)
    
    # Get existing course IDs to avoid duplicates
    existing_ids = set()
    for course_entry in all_courses:
        course_id = course_entry.get('course', {}).get('course_id')
        if course_id:
            existing_ids.add(course_id)
    
    print(f"Existing courses: {len(all_courses)}")
    print(f"Missing courses to add: {len(MISSING_COURSES)}\n")
    
    added = 0
    skipped = 0
    
    for course_id, expected_code, expected_name in MISSING_COURSES:
        if course_id in existing_ids:
            print(f"⏭️  Skipping {expected_code} (already exists)")
            skipped += 1
            continue
        
        print(f"🔍 Fetching {expected_code} (ID: {course_id})...")
        
        course_info, reviews = scrape_course_reviews(course_id, expected_code, expected_name)
        
        if course_info:
            all_courses.append({
                'course': course_info,
                'reviews': reviews,
                'review_count': len(reviews)
            })
            print(f"   ✅ Added: {course_info.get('course_code')} - {course_info.get('name')}")
            print(f"      Reviews: {len(reviews)}")
            added += 1
        else:
            print(f"   ❌ Failed to fetch course {course_id}")
        
        time.sleep(0.5)
    
    # Save updated data
    with open("cs_course_reviews.json", "w") as f:
        json.dump(all_courses, f, indent=4)
    
    print(f"\n{'='*60}")
    print(f"✅ Updated cs_course_reviews.json")
    print(f"   Total courses: {len(all_courses)}")
    print(f"   Added: {added}")
    print(f"   Skipped (duplicates): {skipped}")
    print(f"{'='*60}")

if __name__ == "__main__":
    add_missing_courses()