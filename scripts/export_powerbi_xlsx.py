import os
import pandas as pd


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
OUTPUT_XLSX = os.path.join(ROOT_DIR, "powerbi_youtube_data.xlsx")


def load_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8-sig")


def main():
    videos = load_csv(os.path.join(DATA_DIR, "youtube_videos.csv"))
    comments = load_csv(os.path.join(DATA_DIR, "youtube_comments.csv"))
    sov = load_csv(os.path.join(DATA_DIR, "youtube_monthly_sov.csv"))

    # Ensure types and friendly columns
    if not videos.empty:
        # Parse dates
        if "published_at" in videos.columns:
            videos["published_at"] = pd.to_datetime(videos["published_at"], errors="coerce")
            # Remove timezone for Excel compatibility
            if pd.api.types.is_datetime64_any_dtype(videos["published_at"]):
                try:
                    videos["published_at"] = videos["published_at"].dt.tz_localize(None)
                except Exception:
                    pass
        # Cast numeric
        for col in ["view_count", "like_count", "comment_count"]:
            if col in videos.columns:
                videos[col] = pd.to_numeric(videos[col], errors="coerce").fillna(0).astype(int)

    if not comments.empty:
        if "published_at" in comments.columns:
            comments["published_at"] = pd.to_datetime(comments["published_at"], errors="coerce")
            if pd.api.types.is_datetime64_any_dtype(comments["published_at"]):
                try:
                    comments["published_at"] = comments["published_at"].dt.tz_localize(None)
                except Exception:
                    pass
        for col in ["like_count"]:
            if col in comments.columns:
                comments[col] = pd.to_numeric(comments[col], errors="coerce").fillna(0).astype(int)

    if not sov.empty and "month" in sov.columns:
        sov["month"] = pd.to_datetime(sov["month"], errors="coerce")
        if pd.api.types.is_datetime64_any_dtype(sov["month"]):
            try:
                sov["month"] = sov["month"].dt.tz_localize(None)
            except Exception:
                pass

    with pd.ExcelWriter(OUTPUT_XLSX, engine="xlsxwriter", datetime_format="yyyy-mm-dd", date_format="yyyy-mm-dd") as writer:
        videos.to_excel(writer, index=False, sheet_name="videos")
        comments.to_excel(writer, index=False, sheet_name="comments")
        sov.to_excel(writer, index=False, sheet_name="monthly_sov")

        # Optionally include simple pre-aggregations for convenience
        if not videos.empty:
            brand_summary = videos.groupby("brand", as_index=False).agg(
                videos=("video_id", "nunique"),
                views=("view_count", "sum"),
                likes=("like_count", "sum"),
                comments=("comment_count", "sum"),
            )
            brand_summary.to_excel(writer, index=False, sheet_name="brand_summary")

    print(f"Excel exported: {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()


