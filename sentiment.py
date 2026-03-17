from textblob import TextBlob


def analyze_sentiment(comments: list[str]) -> tuple[float, float, float]:
    if not comments:
        return 0.0, 0.0, 0.0

    positive_count = 0
    neutral_count = 0
    negative_count = 0

    for comment in comments:
        polarity = TextBlob(comment).sentiment.polarity

        if polarity > 0:
            positive_count += 1
        elif polarity < 0:
            negative_count += 1
        else:
            neutral_count += 1

    total = len(comments)

    positive = round((positive_count / total) * 100, 2)
    neutral = round((neutral_count / total) * 100, 2)
    negative = round((negative_count / total) * 100, 2)

    return positive, neutral, negative