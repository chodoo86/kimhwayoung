import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from dateutil import parser as dtparser
from dotenv import load_dotenv
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tqdm import tqdm


# -----------------------------
# Config & Helpers
# -----------------------------

load_dotenv()

API_KEY = os.getenv("AIzaSyA9TK7gQ3YBawc_4tejieleXjziLBH7v50", "")
if not API_KEY:
    raise RuntimeError("Missing YOUTUBE_API_KEY in environment. Create .env with YOUTUBE_API_KEY=...")

# Brands and base query terms
BRANDS = ["배달의민족", "요기요", "쿠팡이츠"]
# You can expand with additional terms per brand if needed

# Search window. Examples: "2024-01-01T00:00:00Z" to now
PUBLISHED_AFTER = os.getenv("PUBLISHED_AFTER", "2024-01-01T00:00:00Z")
PUBLISHED_BEFORE = os.getenv("PUBLISHED_BEFORE", datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))

# Max results per search call (YouTube API allows up to 50)
SEARCH_PAGE_SIZE = int(os.getenv("SEARCH_PAGE_SIZE", "50"))
MAX_SEARCH_PAGES_PER_BRAND = int(os.getenv("MAX_SEARCH_PAGES_PER_BRAND", "10"))  # safety cap

# Max comments per video to fetch (top-level only for simplicity)
MAX_COMMENTS_PER_VIDEO = int(os.getenv("MAX_COMMENTS_PER_VIDEO", "500"))

# Rate limit safety
SLEEP_BETWEEN_CALLS = float(os.getenv("SLEEP_BETWEEN_CALLS", "0.1"))

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def build_client():
    return build("youtube", "v3", developerKey=API_KEY)


# -----------------------------
# API wrappers
# -----------------------------

def search_videos(youtube, query: str, published_after: str, published_before: str,
                  max_pages: int) -> List[Dict]:
    videos = []
    next_token: Optional[str] = None
    pages = 0

    while True:
        if pages >= max_pages:
            break
        try:
            req = youtube.search().list(
                part="id,snippet",
                q=query,
                type="video",
                maxResults=SEARCH_PAGE_SIZE,
                publishedAfter=published_after,
                publishedBefore=published_before,
                relevanceLanguage="ko",
                regionCode="KR",
                order="relevance",
                pageToken=next_token,
            )
            resp = req.execute()
        except HttpError as e:
            # Backoff on quota/4xx
            if e.resp.status in (403, 429, 500, 503):
                time.sleep(2.0)
                continue
            raise

        items = resp.get("items", [])
        for it in items:
            if it.get("id", {}).get("kind") != "youtube#video":
                continue
            videos.append(it)

        next_token = resp.get("nextPageToken")
        pages += 1
        if not next_token:
            break
        time.sleep(SLEEP_BETWEEN_CALLS)
    return videos


def get_videos_details(youtube, video_ids: List[str]) -> List[Dict]:
    details: List[Dict] = []
    # chunk by 50
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        try:
            req = youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(chunk)
            )
            resp = req.execute()
        except HttpError as e:
            if e.resp.status in (403, 429, 500, 503):
                time.sleep(2.0)
                continue
            raise
        details.extend(resp.get("items", []))
        time.sleep(SLEEP_BETWEEN_CALLS)
    return details


def fetch_top_level_comments(youtube, video_id: str, max_comments: int) -> List[Dict]:
    comments: List[Dict] = []
    next_token: Optional[str] = None
    fetched = 0

    while True:
        if fetched >= max_comments:
            break
        page_size = min(100, max_comments - fetched)
        try:
            req = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=page_size,
                order="relevance",
                textFormat="plainText",
                pageToken=next_token
            )
            resp = req.execute()
        except HttpError as e:
            if e.resp.status in (403, 429, 500, 503):
                time.sleep(2.0)
                continue
            # comments disabled or not found
            if e.resp.status in (404,):
                return comments
            raise

        items = resp.get("items", [])
        for it in items:
            snippet = it.get("snippet", {})
            top = snippet.get("topLevelComment", {}).get("snippet", {})
            comments.append({
                "video_id": video_id,
                "comment_id": it.get("id"),
                "author": top.get("authorDisplayName"),
                "text": top.get("textDisplay"),
                "like_count": top.get("likeCount"),
                "published_at": top.get("publishedAt"),
                "updated_at": top.get("updatedAt"),
            })
        fetched += len(items)

        next_token = resp.get("nextPageToken")
        if not next_token:
            break
        time.sleep(SLEEP_BETWEEN_CALLS)
    return comments


# -----------------------------
# Processing
# -----------------------------

def detect_brand(text: str, brands: List[str]) -> Optional[str]:
    if not text:
        return None
    for b in brands:
        if b in text:
            return b
    return None


def aggregate_monthly_sov(videos_df: pd.DataFrame) -> pd.DataFrame:
    if videos_df.empty:
        return pd.DataFrame(columns=["month", "brand", "videos", "views", "likes", "comments", "sov_videos", "sov_views", "sov_likes", "sov_comments"])    
    # month column
    videos_df["month"] = videos_df["published_at"].dt.to_period("M").dt.to_timestamp()

    grouped = videos_df.groupby(["month", "brand"], as_index=False).agg(
        videos=("video_id", "nunique"),
        views=("view_count", "sum"),
        likes=("like_count", "sum"),
        comments=("comment_count", "sum"),
    )

    # compute SoV within month
    def add_share(df: pd.DataFrame, metric: str) -> pd.DataFrame:
        total = df[metric].sum()
        df[f"sov_{metric}"] = df[metric] / total if total > 0 else 0.0
        return df

    result = grouped.groupby("month", group_keys=False).apply(lambda d: (
        add_share(add_share(add_share(add_share(d.copy(), "videos"), "views"), "likes"), "comments")
    ))
    return result


# -----------------------------
# Main
# -----------------------------

def main():
    youtube = build_client()

    all_video_rows: List[Dict] = []
    all_comment_rows: List[Dict] = []

    for brand in BRANDS:
        query = brand
        print(f"Searching videos for brand: {brand}")
        items = search_videos(youtube, query, PUBLISHED_AFTER, PUBLISHED_BEFORE, MAX_SEARCH_PAGES_PER_BRAND)
        video_ids = [it["id"]["videoId"] for it in items if it.get("id", {}).get("videoId")]

        # video details
        details = get_videos_details(youtube, video_ids)

        # rows for videos
        for v in details:
            snippet = v.get("snippet", {})
            stats = v.get("statistics", {})
            published_at = snippet.get("publishedAt")
            title = snippet.get("title", "")
            description = snippet.get("description", "")
            detected_brand = detect_brand(f"{title} {description}", BRANDS)
            row_brand = detected_brand if detected_brand else brand

            all_video_rows.append({
                "brand": row_brand,
                "video_id": v.get("id"),
                "channel_title": snippet.get("channelTitle"),
                "title": title,
                "description": description,
                "published_at": dtparser.parse(published_at) if published_at else None,
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
                "tags": ",".join(snippet.get("tags", [])) if snippet.get("tags") else None,
            })

        # comments per video (top-level)
        print(f"Fetching comments for {len(video_ids)} videos of {brand} (capped per video: {MAX_COMMENTS_PER_VIDEO})")
        for vid in tqdm(video_ids, desc=f"Comments {brand}"):
            comments = fetch_top_level_comments(youtube, vid, MAX_COMMENTS_PER_VIDEO)
            all_comment_rows.extend(comments)

    videos_df = pd.DataFrame(all_video_rows)
    comments_df = pd.DataFrame(all_comment_rows)

    # compute brand label for comments by joining to videos
    if not comments_df.empty:
        if not videos_df.empty:
            comments_df = comments_df.merge(
                videos_df[["video_id", "brand"]], how="left", on="video_id"
            )
        # parse dates
        comments_df["published_at"] = pd.to_datetime(comments_df["published_at"], errors="coerce")

    # monthly SoV from videos
    if not videos_df.empty:
        videos_df["published_at"] = pd.to_datetime(videos_df["published_at"], errors="coerce")
        sov_monthly_df = aggregate_monthly_sov(videos_df)
    else:
        sov_monthly_df = pd.DataFrame()

    # exports
    videos_path = os.path.join(OUTPUT_DIR, "youtube_videos.csv")
    comments_path = os.path.join(OUTPUT_DIR, "youtube_comments.csv")
    sov_path = os.path.join(OUTPUT_DIR, "youtube_monthly_sov.csv")

    videos_df.to_csv(videos_path, index=False, encoding="utf-8-sig")
    comments_df.to_csv(comments_path, index=False, encoding="utf-8-sig")
    sov_monthly_df.to_csv(sov_path, index=False, encoding="utf-8-sig")

    print(f"Saved: {videos_path}\nSaved: {comments_path}\nSaved: {sov_path}")


if __name__ == "__main__":
    main()
