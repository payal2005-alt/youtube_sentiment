from flask import Flask, render_template, request
from urllib.parse import urlparse, parse_qs
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

app = Flask(__name__)

API_KEY = "AIzaSyB4UCcyS90gmwnmJo76DTtZ0uw1pMkeyYs"

analyzer = SentimentIntensityAnalyzer()


def extract_video_id(url):
    parsed_url = urlparse(url)

    if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
        return parse_qs(parsed_url.query).get("v", [None])[0]

    if parsed_url.hostname == "youtu.be":
        return parsed_url.path[1:]

    if parsed_url.hostname in ["m.youtube.com"]:
        return parse_qs(parsed_url.query).get("v", [None])[0]

    return None


def get_youtube_comments(video_id, max_comments=500):
    comments = []
    next_page_token = None
    session = requests.Session()

    while len(comments) < max_comments:
        url = "https://www.googleapis.com/youtube/v3/commentThreads"
        params = {
            "part": "snippet",
            "videoId": video_id,
            "key": API_KEY,
            "maxResults": min(100, max_comments - len(comments)),
            "textFormat": "plainText",
            "order": "relevance"
        }

        if next_page_token:
            params["pageToken"] = next_page_token

        try:
            response = session.get(url, params=params, timeout=10)
            data = response.json()
        except requests.exceptions.Timeout:
            raise Exception("Request timed out. Check your internet or try again later.")
        except requests.exceptions.ConnectionError:
            raise Exception("Could not connect to YouTube API. Check your internet or firewall.")
        except Exception as e:
            raise Exception(f"Network error: {str(e)}")

        if response.status_code != 200:
            error_message = data.get("error", {}).get("message", "Unknown API error")
            raise Exception(f"YouTube API error: {error_message}")

        items = data.get("items", [])
        if not items and not comments:
            raise Exception("No comments found. This video may have comments disabled.")

        for item in items:
            snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
            text = snippet.get("textDisplay", "").strip()
            if text:
                comments.append(text)

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    return comments


def classify_sentiment_vader(text):
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]

    if compound >= 0.05:
        return "Positive"
    elif compound <= -0.05:
        return "Negative"
    return "Neutral"


def analyze_sentiment(comments):
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    analyzed_comments = []

    for comment in comments:
        sentiment = classify_sentiment_vader(comment)

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

    total = len(comments)

    positive_percent = round((positive_count / total) * 100, 2) if total else 0
    negative_percent = round((negative_count / total) * 100, 2) if total else 0
    neutral_percent = round((neutral_count / total) * 100, 2) if total else 0

    return {
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "positive_percent": positive_percent,
        "negative_percent": negative_percent,
        "neutral_percent": neutral_percent,
        "total_comments": total,
        "analyzed_comments": analyzed_comments
    }


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        youtube_url = request.form.get("youtube_url", "").strip()
        video_id = extract_video_id(youtube_url)

        if not video_id:
            return render_template("index.html", error="Invalid YouTube URL")

        try:
            comments = get_youtube_comments(video_id, max_comments=500)
            result = analyze_sentiment(comments)

            return render_template(
                "result.html",
                total_comments=result["total_comments"],
                positive_count=result["positive_count"],
                negative_count=result["negative_count"],
                neutral_count=result["neutral_count"],
                positive_percent=result["positive_percent"],
                negative_percent=result["negative_percent"],
                neutral_percent=result["neutral_percent"],
                analyzed_comments=result["analyzed_comments"]
            )

        except Exception as e:
            return render_template("index.html", error=str(e))

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)