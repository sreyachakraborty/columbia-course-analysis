'''
Filter course reviews to only include courses offered in Spring 2026
'''

import json
import re

# Manual mappings for known mismatches (Spring 2026 code -> CULPA code)
MANUAL_CODE_MAPPINGS = {
    '4232': '4995',  # Advanced Algorithms: W4232 in SIS, 4995 in CULPA
}

def normalize_course_code(code):
    """Extract just the 4-digit course number"""
    if not code:
        return ''
    match = re.search(r'(\d{4})', code)
    return match.group(1) if match else ''

def normalize_name(name):
    """Normalize course name for matching"""
    if not name:
        return ''
    return re.sub(r'[^a-z0-9]', '', name.lower())

def filter_spring_2026_reviews():
    # Load Spring 2026 courses
    with open("spring_2026_cs_courses_simple.json", "r") as f:
        spring_2026 = json.load(f)
    
    # Load all course reviews
    with open("cs_course_reviews.json", "r") as f:
        all_reviews = json.load(f)
    
    print(f"Spring 2026 courses: {len(spring_2026)}")
    print(f"Total courses in CULPA dataset: {len(all_reviews)}")
    
    filtered_reviews = []
    matched = []
    not_found = []
    
    for spring_course in spring_2026:
        spring_code = normalize_course_code(spring_course['course_code'])
        spring_name = spring_course.get('name', '')
        spring_topics = spring_course.get('topics', [])
        
        if not spring_code:
            continue
        
        # Check if there's a manual mapping
        search_codes = [spring_code]
        if spring_code in MANUAL_CODE_MAPPINGS:
            search_codes.append(MANUAL_CODE_MAPPINGS[spring_code])
        
        # Find all CULPA courses with matching course number(s)
        candidates = []
        for course_entry in all_reviews:
            culpa_course = course_entry.get('course', {})
            culpa_code = normalize_course_code(culpa_course.get('course_code', ''))
            
            if culpa_code in search_codes:
                candidates.append(course_entry)
        
        # No matches found
        if not candidates:
            not_found.append(spring_course)
            continue
        
        # Single match — use it
        if len(candidates) == 1:
            filtered_reviews.append(candidates[0])
            matched.append((spring_course, candidates[0]))
            continue
        
        # Multiple matches — try to match on name
        best_match = None
        
        # First try exact name match
        for candidate in candidates:
            culpa_name = candidate.get('course', {}).get('name', '')
            if normalize_name(culpa_name) == normalize_name(spring_name):
                best_match = candidate
                break
        
        # Try matching on topics (for W4995/E6998)
        if not best_match and spring_topics:
            for topic in spring_topics:
                for candidate in candidates:
                    culpa_name = candidate.get('course', {}).get('name', '')
                    if normalize_name(topic) in normalize_name(culpa_name) or \
                       normalize_name(culpa_name) in normalize_name(topic):
                        best_match = candidate
                        break
                if best_match:
                    break
        
        # Try partial name match
        if not best_match:
            for candidate in candidates:
                culpa_name = candidate.get('course', {}).get('name', '')
                if normalize_name(spring_name) in normalize_name(culpa_name) or \
                   normalize_name(culpa_name) in normalize_name(spring_name):
                    best_match = candidate
                    break
        
        # Still no match — take the one with most reviews
        if not best_match:
            best_match = max(candidates, key=lambda x: len(x.get('reviews', [])))
        
        filtered_reviews.append(best_match)
        matched.append((spring_course, best_match))
    
    print(f"\nMatched: {len(matched)}")
    print(f"Not found: {len(not_found)}")
    
    if not_found:
        print(f"\n❌ NOT IN CULPA DATASET ({len(not_found)}):")
        for course in not_found:
            full_code = course.get('course_code', 'Unknown')
            name = course.get('name', 'Unknown')
            instructors = ', '.join(course.get('instructors', [])) or 'TBA'
            print(f"  - {full_code}: {name}")
            print(f"      Instructor(s): {instructors}")
    
    # Save filtered reviews
    with open("spring_2026_course_reviews.json", "w") as f:
        json.dump(filtered_reviews, f, indent=4)
    
    total_reviews = sum(len(c.get('reviews', [])) for c in filtered_reviews)
    
    print(f"\n{'='*60}")
    print(f"✅ Saved spring_2026_course_reviews.json")
    print(f"   Courses: {len(filtered_reviews)}")
    print(f"   Total reviews: {total_reviews}")
    print(f"{'='*60}")
    
    return filtered_reviews


if __name__ == "__main__":
    filter_spring_2026_reviews()