import json

with open("jae_reviews.json", "r") as f:
    data = json.load(f)

cleaned = []
for r in data:
    cleaned.append({
        "course": r["course"] if r["course"] else None,
        "date": r["date"].strip() if r["date"] else None,
        "text": " ".join(r["text"].split()) if r["text"] else ""
    })

with open("clean_reviews.json", "w") as f:
    json.dump(cleaned, f, indent=4)

print("Cleaned data written to clean_reviews.json")
