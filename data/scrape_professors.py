'''
This file extends scrape.py by trying to scrape all the pages for each professor in the CS department.
I first tried to figure out the API calls corresponding to the department page and each professor
page so i could figure out a way to automate this.

This is the GET request for the list of all departments
https://culpa.info/api/departments/all
This gave a JSON file with department names, IDs and codes, e.g. COMS is ID 7

This is the GET request that gets the list of all courses in the COMS department
https://culpa.info/api/departments/7/courses
JSON file with elements like course code, course ID, department ID, name, and status (???)

This is the GET request that gets the list of all professors in the COMS department
https://culpa.info/api/departments/7/professors
each prof has first_name, last_name, nuggest (boolean), professor_id, status, and uni
'''

import requests
import json
import time

BASE_URL = "https://culpa.info/api"
CS_DEPARTMENT_ID = 7  # COMS department ID

def get_cs_professors():
    """Get all professors in the CS department"""
    print("Fetching CS department professors...")
    response = requests.get(f"{BASE_URL}/departments/{CS_DEPARTMENT_ID}/professors")
    
    if response.status_code != 200:
        print(f"Error fetching professors: {response.status_code}")
        return []
    
    professors = response.json()
    print(f"Found {len(professors)} CS professors")
    return professors

def scrape_professor_reviews(professor_id):
    """Scrape all reviews for a single professor"""
    all_reviews = []
    seen_ids = set()
    page = 1
    
    while True:
        response = requests.get(
            f"{BASE_URL}/review/professor/{professor_id}",
            params={'page': page, 'sort_key': 'null', 'course_filter': 'null'}
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

def scrape_cs_reviews():
    """Scrape reviews for all CS professors"""
    # Get CS professors
    professors = get_cs_professors()
    
    if not professors:
        print("No professors found!")
        return
    
    print(f"\nStarting to scrape reviews for {len(professors)} CS professors...\n")
    
    all_data = []
    total_reviews = 0
    
    for i, prof in enumerate(professors, 1):
        prof_id = prof.get('professor_id')
        first_name = prof.get('first_name', '')
        last_name = prof.get('last_name', '')
        uni = prof.get('uni', '')
        
        print(f"[{i}/{len(professors)}] {first_name} {last_name} ({uni}) - ID: {prof_id}")
        
        reviews = scrape_professor_reviews(prof_id)
        
        if reviews:
            print(f"  ✓ Found {len(reviews)} reviews")
            all_data.append({
                'professor': prof,
                'reviews': reviews,
                'review_count': len(reviews)
            })
            total_reviews += len(reviews)
        else:
            print(f"  ✗ No reviews")
        
        # Save progress every 10 professors
        if i % 10 == 0:
            with open("cs_reviews_progress.json", "w") as f:
                json.dump(all_data, f, indent=4)
            print(f"  💾 Progress saved ({i}/{len(professors)}, {total_reviews} reviews so far)\n")
        
        time.sleep(0.5)  # Be nice to the server
    
    # Final save
    with open("cs_reviews.json", "w") as f:
        json.dump(all_data, f, indent=4)
    
    print(f"\n{'='*60}")
    print(f"✅ Complete!")
    print(f"   Professors with reviews: {len(all_data)}")
    print(f"   Total reviews scraped: {total_reviews}")
    print(f"   Saved to: cs_reviews.json")
    print(f"{'='*60}")

if __name__ == "__main__":
    scrape_cs_reviews()