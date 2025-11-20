'''
Merge duplicate professors based on manual decisions.

After running deduplicate.py to identify duplicates and checking which courses
they teach, update the merge_map below with your decisions, then run this script
to create clean_cs_reviews.json

Original professor entries:  148
After merging:               146
Professors merged:           2
Total reviews:               1352
Saved to:                    clean_cs_reviews.json
'''

import json

def merge_professors(input_file="cs_reviews.json", output_file="merged_cs_reviews.json"):
    """
    Merge duplicate professors based on manual merge decisions
    """
    
    # ============= EDIT THIS MERGE MAP =============
    # Format: old_id -> primary_id (which ID to merge INTO)
    # Example: If Donald Ferguson has IDs 6653 and 13551, and you want to keep 6653:
    #          13551: 6653  means "merge 13551 into 6653"
    
    merge_map = {
        # Add your merge decisions here
        # old_id: primary_id,
        6653 : 13551,
        13070 : 13159
    }
    # ===============================================
    
    if not merge_map:
        print("⚠️  WARNING: merge_map is empty!")
        print("   Add your merge decisions to the merge_map dictionary in merge.py")
        return
    
    # Load data
    with open(input_file, "r") as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} professor entries from {input_file}\n")
    print(f"Applying {len(merge_map)} merges...\n")
    
    # Group data by professor ID (after mapping)
    merged_data = {}
    
    for item in data:
        prof = item['professor']
        original_id = prof['professor_id']
        
        # Get the ID to use (mapped or original)
        target_id = merge_map.get(original_id, original_id)
        
        # Initialize if first time seeing this target_id
        if target_id not in merged_data:
            merged_data[target_id] = {
                'professor': prof.copy(),
                'reviews': [],
                'review_ids': set()
            }
            # Update professor_id to the primary one
            merged_data[target_id]['professor']['professor_id'] = target_id
        
        # Add reviews (avoid duplicates by review_id)
        for review in item['reviews']:
            review_id = review.get('review_id')
            if review_id and review_id not in merged_data[target_id]['review_ids']:
                merged_data[target_id]['reviews'].append(review)
                merged_data[target_id]['review_ids'].add(review_id)
    
    # Convert to final format
    clean_data = []
    for target_id, merged_item in merged_data.items():
        clean_data.append({
            'professor': merged_item['professor'],
            'review_count': len(merged_item['reviews']),
            'reviews': merged_item['reviews']
        })
    
    # Sort by last name, then first name
    clean_data.sort(key=lambda x: (
        x['professor']['last_name'],
        x['professor']['first_name']
    ))
    
    # Save to file
    with open(output_file, "w") as f:
        json.dump(clean_data, f, indent=4)
    
    # Print summary
    total_reviews = sum(item['review_count'] for item in clean_data)
    
    print(f"{'='*70}")
    print(f"✅ MERGE COMPLETE")
    print(f"{'='*70}")
    print(f"Original professor entries:  {len(data)}")
    print(f"After merging:               {len(clean_data)}")
    print(f"Professors merged:           {len(data) - len(clean_data)}")
    print(f"Total reviews:               {total_reviews}")
    print(f"Saved to:                    {output_file}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    merge_professors()