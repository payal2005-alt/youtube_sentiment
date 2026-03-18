from flask import Flask, render_template, request
from textblob import TextBlob
from urllib.parse import urlparse, parse_qs
import requests
import re

app = Flask(__name__)

API_KEY = "AIzaSyB4UCcyS90gmwnmJo76DTtZ0uw1pMkeyYs"


def extract_video_id(url):
    parsed_url = urlparse(url)

    if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
        return parse_qs(parsed_url.query).get("v", [None])[0]

    if parsed_url.hostname == "youtu.be":
        return parsed_url.path[1:]

    return None


def clean_comment(text):
    if not text:
        return ""
    text = re.sub(r"<.*?>", "", text)
    return text.strip()


def get_youtube_comments(video_id, max_comments=500):
    comments = []
    next_page_token = None

    while len(comments) < max_comments:
        url = "https://www.googleapis.com/youtube/v3/commentThreads"
        params = {
            "part": "snippet",
            "videoId": video_id,
            "key": API_KEY,
            "maxResults": min(100, max_comments - len(comments))
        }

        if next_page_token:
            params["pageToken"] = next_page_token

        response = requests.get(url, params=params)
        data = response.json()

        if "items" not in data:
            break

        for item in data["items"]:
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comment = clean_comment(comment)
            if comment:
                comments.append(comment)

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    return comments


def detect_sentiment(comment):
    text = comment.strip()

    if not text:
        return "Neutral"

    polarity = TextBlob(text).sentiment.polarity

    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    youtube_url = request.form.get("youtube_url", "").strip()
    video_id = extract_video_id(youtube_url)

    if not video_id:
        return "Invalid YouTube URL"

    comments = get_youtube_comments(video_id, max_comments=500)

    analyzed_comments = []
    positive_count = 0
    neutral_count = 0
    negative_count = 0

    for comment in comments:
        sentiment = detect_sentiment(comment)

        if sentiment == "Positive":
            positive_count += 1
        elif sentiment == "Negative":
            negative_count += 1
        else:
            neutral_count += 1

        analyzed_comments.append({
            "text": comment,
            "sentiment": sentiment
        })

    total_comments = len(analyzed_comments)

    if total_comments == 0:
        positive_percentage = 0
        neutral_percentage = 0
        negative_percentage = 0
    else:
        positive_percentage = round((positive_count / total_comments) * 100, 2)
        neutral_percentage = round((neutral_count / total_comments) * 100, 2)
        negative_percentage = round((negative_count / total_comments) * 100, 2)

    return render_template(
        "result.html",
        total_comments=total_comments,
        positive_count=positive_count,
        neutral_count=neutral_count,
        negative_count=negative_count,
        positive_percentage=positive_percentage,
        neutral_percentage=neutral_percentage,
        negative_percentage=negative_percentage,
        analyzed_comments=analyzed_comments
    )


if __name__ == "__main__":
    app.run(debug=True)