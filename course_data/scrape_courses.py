'''
This file scrapes all reviews for each course in the CS department.

API endpoints:
- https://culpa.info/api/departments/7/courses - list of all CS courses
- https://culpa.info/api/review/course/{course_id} - reviews for a specific course
'''

import requests
import json
import time

BASE_URL = "https://culpa.info/api"
CS_DEPARTMENT_ID = 7  # COMS department ID

def get_cs_courses():
    """Get all courses in the CS department"""
    print("Fetching CS department courses...")
    response = requests.get(f"{BASE_URL}/departments/{CS_DEPARTMENT_ID}/courses")
    
    if response.status_code != 200:
        print(f"Error fetching courses: {response.status_code}")
        return []
    
    courses = response.json()
    print(f"Found {len(courses)} CS courses")
    return courses

def scrape_course_reviews(course_id):
    """Scrape all reviews for a single course"""
    all_reviews = []
    seen_ids = set()
    page = 1
    
    while True:
        response = requests.get(
            f"{BASE_URL}/review/course/{course_id}",
            params={'page': page, 'sort_key': 'null', 'professor_filter': 'null'}
        )
        
        if response.status_code != 200:
            break
        
        data = response.json()
        reviews = data.get('reviews', [])
        
        if not reviews:
            break
        
        # Add unique reviews
        for review in reviews:
            review_id = review.get('review_id')
            if review_id and review_id not in seen_ids:
                all_reviews.append(review)
                seen_ids.add(review_id)
        
        page += 1
        time.sleep(0.3)
    
    return all_reviews

def scrape_cs_course_reviews():
    """Scrape reviews for all CS courses"""
    # Get CS courses
    courses = get_cs_courses()
    
    if not courses:
        print("No courses found!")
        return
    
    print(f"\nStarting to scrape reviews for {len(courses)} CS courses...\n")
    
    all_data = []
    total_reviews = 0
    
    for i, course in enumerate(courses, 1):
        course_id = course.get('course_id')
        course_code = course.get('course_code', '')
        course_name = course.get('name', '')
        
        print(f"[{i}/{len(courses)}] {course_code} - {course_name} - ID: {course_id}")
        
        reviews = scrape_course_reviews(course_id)
        
        if reviews:
            print(f"  ✓ Found {len(reviews)} reviews")
            all_data.append({
                'course': course,
                'reviews': reviews,
                'review_count': len(reviews)
            })
            total_reviews += len(reviews)
        else:
            print(f"  ✗ No reviews")
        
        # Save progress every 10 courses
        if i % 10 == 0:
            with open("cs_course_reviews_progress.json", "w") as f:
                json.dump(all_data, f, indent=4)
            print(f"  💾 Progress saved ({i}/{len(courses)}, {total_reviews} reviews so far)\n")
        
        time.sleep(0.5)  # Be nice to the server
    
    # Final save
    with open("cs_course_reviews.json", "w") as f:
        json.dump(all_data, f, indent=4)
    
    print(f"\n{'='*60}")
    print(f"✅ Complete!")
    print(f"   Courses with reviews: {len(all_data)}")
    print(f"   Total reviews scraped: {total_reviews}")
    print(f"   Saved to: cs_course_reviews.json")
    print(f"{'='*60}")

if __name__ == "__main__":
    scrape_cs_course_reviews()