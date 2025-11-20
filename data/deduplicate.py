'''
Fixing the issue that there were some professors with multiple professor IDs.
I want to aggregate all the reviews for the same professor under the same 
section of the JSON file. 

I found matching first_name,last_name pairs with different professor IDs, and then 
checked my cs_reviews.json to check what courses the two professor IDs taught. If
they were similar/the same, I assume they are the same professor and aggregate it the 
reviews in the new clean_cs_reviews.json file as under the same professor (just choose
one of the prof IDs)
'''

import json
from collections import defaultdict

def find_duplicate_names(filename="cs_reviews.json"):
    """Find and print professors with the same first and last name, showing courses"""
    
    # Load data
    with open(filename, "r") as f:
        data = json.load(f)
    
    # Group by full name
    name_to_profs = defaultdict(list)
    
    for item in data:
        prof = item['professor']
        full_name = f"{prof['first_name']} {prof['last_name']}"
        
        # Get courses from reviews
        courses = set()
        for review in item.get('reviews', []):
            course_header = review.get('course_header', {})
            course_code = course_header.get('course_code')
            if course_code:
                courses.add(course_code)
        
        name_to_profs[full_name].append({
            'id': prof['professor_id'],
            'uni': prof.get('uni', 'N/A'),
            'nugget': prof.get('nugget', False),
            'review_count': item.get('review_count', 0),
            'courses': sorted(courses)
        })
    
    # Find duplicates (names with more than 1 ID)
    duplicates = {name: profs for name, profs in name_to_profs.items() if len(profs) > 1}
    
    # Print results
    if duplicates:
        print(f"Found {len(duplicates)} names with multiple IDs:\n")
        print("="*70)
        for name, profs in sorted(duplicates.items()):
            print(f"\n{name}")
            print("-"*70)
            print(f"{'ID':<10} {'UNI':<15} {'Reviews':<10} {'Nugget'}")
            print("-"*70)
            for p in profs:
                nugget = "⭐" if p['nugget'] else ""
                review_count = p['review_count'] if p['review_count'] is not None else 0
                uni = p['uni'] if p['uni'] is not None else 'N/A'
                print(f"{p['id']:<10} {uni:<15} {review_count:<10} {nugget}")
                
                # Print courses
                if p['courses']:
                    print(f"           Courses: {', '.join(p['courses'])}")
                else:
                    print(f"           Courses: None listed")
                print()
        print("="*70)
    else:
        print("No duplicate names found!")

if __name__ == "__main__":
    find_duplicate_names()