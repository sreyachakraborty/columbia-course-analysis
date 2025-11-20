import json
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from tqdm import tqdm

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"

def load_reviews(path="clean_reviews.json"):
    with open(path, "r") as f:
        return json.load(f)

def save_reviews(data, path="reviews_with_sentiment.json"):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def analyze_sentiment(reviews):
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

    results = []
    for r in tqdm(reviews, desc="Analyzing reviews"):
        text = r["text"]
        if not text:
            r["sentiment"] = {"label": "neutral", "score": 0.0}
            results.append(r)
            continue

        inputs = tokenizer(
            text,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )

        with torch.no_grad():
            logits = model(**inputs).logits
            probs = torch.softmax(logits, dim=1)[0]

        positive_score = float(probs[1])
        negative_score = float(probs[0])
        label = "positive" if positive_score >= 0.6 else \
                "negative" if negative_score >= 0.6 else "neutral"

        r["sentiment"] = {
            "label": label,
            "positive_score": positive_score,
            "negative_score": negative_score,
        }
        results.append(r)

    return results

def summarize(reviews):
    summary = {"positive": 0, "neutral": 0, "negative": 0}
    for r in reviews:
        summary[r["sentiment"]["label"]] += 1
    return summary

def main():
    reviews = load_reviews("clean_reviews.json")
    print(f"Loaded {len(reviews)} reviews.")

    annotated = analyze_sentiment(reviews)
    save_reviews(annotated)

    stats = summarize(annotated)
    print("\nSentiment Summary:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
