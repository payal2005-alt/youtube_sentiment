import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

API_KEY = "AIzaSyB4UCcyS90gmwnmJo76DTtZ0uw1pMkeyYs"


def get_video_id(url: str) -> str | None:
    patterns = [
        r"(?:v=)([0-9A-Za-z_-]{11})",
        r"(?:youtu\.be/)([0-9A-Za-z_-]{11})",
        r"(?:shorts/)([0-9A-Za-z_-]{11})",
        r"(?:embed/)([0-9A-Za-z_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def fetch_comments(video_url: str, max_comments: int = 500) -> list[str]:
    video_id = get_video_id(video_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL. Please enter a valid video link.")

    if API_KEY == "PASTE_YOUR_NEW_API_KEY_HERE":
        raise ValueError("Please add your YouTube API key in youtube_utils.py")

    youtube = build("youtube", "v3", developerKey=API_KEY)

    comments = []
    next_page_token = None

    try:
        while len(comments) < max_comments:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(100, max_comments - len(comments)),
                pageToken=next_page_token,
                textFormat="plainText",
                order="relevance"
            )

            response = request.execute()
            items = response.get("items", [])

            if not items:
                break

            for item in items:
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                text = snippet.get("textDisplay", "").strip()

                if text:
                    comments.append(text)

                if len(comments) >= max_comments:
                    break

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

    except HttpError as e:
        raise ValueError(f"YouTube API error: {e}")

    return comments