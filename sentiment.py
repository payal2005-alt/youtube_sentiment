from textblob import TextBlob

def analyze_comments(comments):
    positive = 0
    negative = 0
    neutral = 0

    for comment in comments:
        polarity = TextBlob(comment).sentiment.polarity

        if polarity > 0:
            positive += 1
        elif polarity < 0:
            negative += 1
        else:
            neutral += 1

    return {
        "total": len(comments),
        "positive": positive,
        "negative": negative,
        "neutral": neutral
    }