"""
Fetches YouTube comments about a specific fragrance.
Uses the official YouTube Data API v3.
"""

import os
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()


def get_youtube_client():
    """Initialise and return an authenticated YouTube client."""
    return build(
        "youtube", "v3",
        developerKey=os.getenv("YOUTUBE_API_KEY")
    )


def fetch_youtube_comments(
    fragrance_name: str,
    brand: str,
    max_videos: int = 3,
    max_comments_per_video: int = 30
) -> list[dict]:
    """
    Search YouTube for fragrance review videos and fetch
    their top comments. Returns comments with engagement signals.
    """
    youtube = get_youtube_client()
    query = f"{brand} {fragrance_name} fragrance review"
    results = []

    try:
        search_response = youtube.search().list(
            q=query,
            part="snippet",
            maxResults=max_videos,
            type="video",
            relevanceLanguage="en"
        ).execute()

        video_ids = [
            item["id"]["videoId"]
            for item in search_response.get("items", [])
        ]

        for video_id in video_ids:
            try:
                comments_response = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=max_comments_per_video,
                    order="relevance"
                ).execute()

                for item in comments_response.get("items", []):
                    comment = item["snippet"]["topLevelComment"]
                    snippet = comment["snippet"]
                    like_count = snippet.get("likeCount", 0)

                    if like_count < 2:
                        continue

                    results.append({
                        "source": "youtube_comment",
                        "text": snippet["textDisplay"][:500],
                        "likes": like_count,
                        "video_id": video_id
                    })

            except Exception as e:
                print(f"Error fetching comments for "
                      f"video {video_id}: {e}")
                continue

    except Exception as e:
        print(f"YouTube fetch error: {e}")

    return results


def format_youtube_for_prompt(content: list[dict]) -> str:
    """
    Format YouTube comments into a string for the Claude prompt.
    Each entry tagged with engagement signals.
    """
    lines = []
    for item in content:
        lines.append(
            f"[{item['likes']} likes, YouTube Comment] "
            f"{item['text']}"
        )
    return "\n\n".join(lines)