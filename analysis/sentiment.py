from transformers import pipeline

# Create the pipeline ONCE (slow, but only the first time)
sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

def analyze_sentiment(text):
    # Pipeline can accept a list, but we send one at a time
    result = sentiment_pipeline(text[:512])[0]  # truncate long text to 512 chars
    label = result['label'].lower()  # 'positive' or 'negative'
    score = result['score']
    # For this app, treat "neutral" if the score is between 0.45 and 0.55
    if label == "positive" and score < 0.55:
        label = "neutral"
    elif label == "negative" and score < 0.55:
        label = "neutral"
    return label, float(score)
