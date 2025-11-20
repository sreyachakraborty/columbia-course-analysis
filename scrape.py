'''
steps: I am implementing the strategy from this article:
https://medium.com/@adeltoft/how-to-scrape-a-page-with-a-load-more-button-718c28a2956c
open the CULPA page, right click + inspect for developer tools, then check
the network tab specifically the "Fetch/XHR" filter (which shows API requests)
Click Load more, look for the API request. Click on it to see the response
Test the API
I ended up finding API calls such as: https://culpa.info/api/review/professor/3509?page=1&sort_key=null&course_filter=null
to fetch the JSON files.
Each API call returns something like:
{
  "number_of_reviews": 61,           // Total number of reviews
  "reviews": [...],                  // Array of review objects
  "reviews_spotlight": {...}         // Special highlighted reviews
}

And then each individual review in the array is an object like this:
{
  "review_id": 86419,
  "submission_date": "2025-01-13T13:43:22",
  "rating": 5,                         // 1-5 star rating
  
  "content": "I stepped into 3157...", // Main review text
  "workload": "TLDR: Grades may...",   // Workload description
  
  "agree_count": 4,                    // Upvotes
  "disagree_count": 4,                 // Downvotes
  "funny_count": 0,                    // Funny reactions
  
  "professor_header": {
    "professor_id": 3509,
    "first_name": "Jae",
    "last_name": "Lee",
    "uni": "jwl3",
    "nugget": 1                        // Not sure what this is
  },
  
  "course_header": {
    "course_id": 4758,
    "course_code": "COMS W3157",
    "course_name": "Advanced Programming"
  }
}

And there is reviews spotlight too:
"reviews_spotlight": {
  "agreed_review": {
    // The review with the most "agree" votes
    "agree_count": 140,
    "content": "...",
    // ... (same structure as regular review)
  },
  
  "controversial_review": {
    // The review with the most mixed votes (lots of agrees + disagrees)
    "agree_count": 55,
    "disagree_count": 62,
    "content": "...",
    // ... (same structure as regular review)
  }
}

I ran into an issue where the scraper was not scraping all reviews.
This is because there is a spotlight review and I was only checking the reviews array
Every page has the same spotlight review potentially, so in order to make sure
my JSON file does not have duplicates I will track the review IDs that I have
already scraped using a set. 

I found that it turned out that the mismatch between expected reviews 
and actual reviews scraped was not truly an error since even after the more robust
duplicate checking and checking both reviews and spotlight, it only gave 60. 
However, I kept the set to check for duplicates for robustness 
'''

# This script will aggregate all the review objects for a given professor into a JSON file using the CULPA API
import requests
import json
import time

PROFESSOR_ID = "3509"
BASE_URL = f"https://culpa.info/api/review/professor/{PROFESSOR_ID}"

def scrape_culpa_api():
    all_reviews = []
    seen_ids = set()
    page = 1
    
    while True:
        print(f"Fetching page {page}...")
        
        response = requests.get(BASE_URL, params={
            'page': page,
            'sort_key': 'null',
            'course_filter': 'null'
        })
        
        if response.status_code != 200:
            print(f"Error: Status {response.status_code}")
            break
        
        data = response.json()
        
        # Collect all reviews from this page (regular + spotlight)
        reviews_to_check = []
        
        # Add regular reviews
        regular_reviews = data.get('reviews', [])
        reviews_to_check.extend(regular_reviews)
        
        # Add spotlight reviews
        if 'reviews_spotlight' in data:
            spotlight = data['reviews_spotlight']
            if 'agreed_review' in spotlight and spotlight['agreed_review']:
                reviews_to_check.append(spotlight['agreed_review'])
            if 'controversial_review' in spotlight and spotlight['controversial_review']:
                reviews_to_check.append(spotlight['controversial_review'])
        
        # If no reviews at all, we're done
        if not reviews_to_check:
            print("No more reviews!")
            break
        
        # Add only unique reviews
        added_count = 0
        for review in reviews_to_check:
            review_id = review.get('review_id')
            if review_id and review_id not in seen_ids:
                all_reviews.append(review)
                seen_ids.add(review_id)
                added_count += 1
        
        print(f"  Added {added_count} new reviews (total: {len(all_reviews)})")
        
        # Stop if we got no regular reviews (even if spotlight exists)
        if not regular_reviews:
            print("No more regular reviews!")
            break
        
        page += 1
        time.sleep(0.5)
    
    print(f"\n✅ Saved {len(all_reviews)} unique reviews to jae_reviews.json")
    
    with open("jae_reviews.json", "w") as f:
        json.dump(all_reviews, f, indent=4)

if __name__ == "__main__":
    scrape_culpa_api()