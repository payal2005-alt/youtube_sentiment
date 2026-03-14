from flask import Flask, render_template, request
from youtube_utils import extract_video_id, get_comments
from sentiment import analyze_comments

app = Flask(__name__)

API_KEY = "AIzaSyBUpNUAG5_ETpJsDd88TabdRKF7BbKxS1Q"


@app.route("/", methods=["GET", "POST"])
def home():
    comments = None
    summary = None
    error = None

    if request.method == "POST":
        video_url = request.form.get("youtube_url")

        if not video_url:
            error = "Please enter a YouTube URL."
        else:
            video_id = extract_video_id(video_url)

            if not video_id:
                error = "Invalid YouTube URL."
            else:
                try:
                    comments = get_comments(video_id, API_KEY, max_comments=500)
                    print("Fetched comments:", len(comments))
                    summary = analyze_comments(comments)
                except Exception as e:
                    error = f"Error: {str(e)}"

    return render_template("index.html", comments=comments, summary=summary, error=error)


if __name__ == "__main__":
    app.run(debug=True)