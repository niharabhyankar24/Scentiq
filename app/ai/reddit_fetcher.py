"""
Fetches Reddit posts and comments about a specific fragrance
using the Arctic Shift public archive. No API key required.
"""

import httpx
from urllib.parse import quote


ARCTIC_BASE = "https://arctic-shift.photon-reddit.com/api"
SUBREDDITS = [
    "fragrance",
    "masculinefragrance",
    "Colognes",
    "DecantX",
    "IndianFragranceAddicts",
    "DesiFragranceAddicts"
]

def fetch_posts(
    fragrance_name: str,
    brand: str,
    limit: int = 5
) -> list[dict]:
    """
    Search multiple subreddits for posts about a fragrance
    via Arctic Shift. Returns merged results with engagement
    signals, sorted by score descending.
    """
    query = f"{brand} {fragrance_name}"
    all_posts = []

    for subreddit in SUBREDDITS:
        url = (
            f"{ARCTIC_BASE}/posts/search"
            f"?subreddit={subreddit}"
            f"&q={quote(query)}"
            f"&limit={limit}"
            f"&sort=score"
        )
        try:
            response = httpx.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            posts = data.get("data", [])
            all_posts.extend(posts)
        except Exception as e:
            print(f"Arctic Shift error for "
                  f"r/{subreddit}: {e}")
            continue

    all_posts.sort(key=lambda p: p.get("score", 0), reverse=True)
    return all_posts

def fetch_comments(post_id: str, limit: int = 10) -> list[dict]:
    """
    Fetch top comments for a specific Reddit post
    via Arctic Shift using the post ID.
    """
    url = (
        f"{ARCTIC_BASE}/comments/search"
        f"?link_id={post_id}"
        f"&limit={limit}"
        f"&sort=score"
    )
    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print(f"Arctic Shift comment fetch error: {e}")
        return []

def fetch_reddit_content(
    fragrance_name: str,
    brand: str,
    max_posts: int = 8,
    max_comments_per_post: int = 5
) -> list[dict]:
    """
    Full Reddit content fetch pipeline. Fetches posts and
    their top comments. Filters low engagement content.
    Returns structured list with engagement signals.
    """
    posts = fetch_posts(fragrance_name, brand, limit=max_posts)
    results = []

    for post in posts:
        score = post.get("score", 0)
        if score < 5:
            continue

        results.append({
            "source": "reddit_post",
            "title": post.get("title", ""),
            "text": post.get("selftext", "")[:1000],
            "upvotes": score,
            "comment_count": post.get("num_comments", 0),
            "post_id": post.get("id", ""),
            "url": f"https://reddit.com{post.get('permalink', '')}"
        })

        post_id = post.get("id")
        if not post_id:
            continue

        comments = fetch_comments(
            post_id,
            limit=max_comments_per_post
        )

        for comment in comments:
            comment_score = comment.get("score", 0)
            if comment_score < 3:
                continue
            results.append({
                "source": "reddit_comment",
                "title": "",
                "text": comment.get("body", "")[:500],
                "upvotes": comment_score,
                "comment_count": 0,
                "post_id": post_id,
                "url": (
                    f"https://reddit.com"
                    f"{post.get('permalink', '')}"
                    f"{comment.get('id', '')}"
                )
            })

    return results


def format_reddit_for_prompt(content: list[dict]) -> str:
    """
    Format Reddit content into a prompt-ready string.
    Each entry tagged with source and engagement signals.
    """
    if not content:
        return ""

    lines = []
    for item in content:
        label = (
            "Reddit Post" if item["source"] == "reddit_post"
            else "Reddit Comment"
        )
        text = f"{item.get('title', '')} {item.get('text', '')}"
        text = text.strip()
        if not text:
            continue
        lines.append(
            f"[{item['upvotes']} upvotes, {label}] {text}"
        )

    return "\n\n".join(lines)