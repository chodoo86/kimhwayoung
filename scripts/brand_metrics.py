import os
from datetime import datetime
import pandas as pd


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
VIDEOS_CSV = os.path.join(DATA_DIR, "youtube_videos.csv")
COMMENTS_CSV = os.path.join(DATA_DIR, "youtube_comments.csv")
SOV_CSV = os.path.join(DATA_DIR, "youtube_monthly_sov.csv")
REPORT_MD = os.path.join(ROOT_DIR, "ANALYSIS.md")


def load_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8-sig")


def compute_brand_proxies(videos_df: pd.DataFrame, comments_df: pd.DataFrame, sov_df: pd.DataFrame) -> dict:
    results = {}
    if videos_df.empty:
        return results

    # Coerce numeric
    for col in ["view_count", "like_count", "comment_count"]:
        if col in videos_df.columns:
            videos_df[col] = pd.to_numeric(videos_df[col], errors="coerce").fillna(0)

    # Interest proxies: volume and reach
    interest = (
        videos_df.groupby("brand", as_index=False)
        .agg(videos=("video_id", "nunique"), views=("view_count", "sum"))
        .sort_values("views", ascending=False)
    )

    # Preference proxies: engagement normalized by views
    pref = (
        videos_df.groupby("brand", as_index=False)
        .agg(views=("view_count", "sum"), likes=("like_count", "sum"), comments=("comment_count", "sum"))
    )
    pref["likes_per_1k_views"] = (pref["likes"] / pref["views"].replace(0, pd.NA) * 1000).fillna(0).round(3)
    pref["comments_per_1k_views"] = (pref["comments"] / pref["views"].replace(0, pd.NA) * 1000).fillna(0).round(3)
    pref = pref[["brand", "likes_per_1k_views", "comments_per_1k_views"]].sort_values("likes_per_1k_views", ascending=False)

    # Perception proxies from comments: avg likes per comment (as weak proxy)
    perception = pd.DataFrame()
    if not comments_df.empty:
        # Ensure like_count numeric
        if "like_count" in comments_df.columns:
            comments_df["like_count"] = pd.to_numeric(comments_df["like_count"], errors="coerce").fillna(0)
        # Ensure brand on comments
        if "brand" not in comments_df.columns and not videos_df.empty:
            comments_df = comments_df.merge(videos_df[["video_id", "brand"]], how="left", on="video_id")
        if "brand" in comments_df.columns:
            perception = (
                comments_df.groupby("brand", as_index=False)
                .agg(avg_comment_likes=("like_count", "mean"), median_comment_likes=("like_count", "median"), total_top_level_comments=("comment_id", "count"))
            )
            perception["avg_comment_likes"] = perception["avg_comment_likes"].round(3)
            perception["median_comment_likes"] = perception["median_comment_likes"].round(3)

    # Latest month SoV snapshot
    sov_latest = pd.DataFrame()
    if not sov_df.empty and "month" in sov_df.columns:
        sov_df["month"] = pd.to_datetime(sov_df["month"], errors="coerce")
        latest = sov_df["month"].max()
        if pd.notna(latest):
            sov_latest = sov_df[sov_df["month"] == latest][["brand", "sov_videos", "sov_views", "sov_likes", "sov_comments"]].copy()
            for col in ["sov_videos", "sov_views", "sov_likes", "sov_comments"]:
                sov_latest[col] = (pd.to_numeric(sov_latest[col], errors="coerce").fillna(0) * 100).round(2)
            sov_latest = sov_latest.sort_values("sov_views", ascending=False)

    results["interest"] = interest
    results["preference"] = pref
    results["perception"] = perception
    results["sov_latest"] = sov_latest
    return results


def df_to_md(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df is None or df.empty:
        return "(no data)"
    df_show = df.head(max_rows)
    headers = list(df_show.columns)
    lines = ["| " + " | ".join(map(str, headers)) + " |",
             "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in df_show.iterrows():
        cells = [str(row[h]) for h in headers]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def append_report(res: dict):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("## 브랜드 관심도/선호도/인식 비교")
    lines.append(f"- 생성시각: {ts}")
    lines.append("")
    lines.append("### 방법")
    lines.append("- 관심도(Interest): 영상수, 총 조회수 (규모/도달력)")
    lines.append("- 선호도(Preference): likes/1k views, comments/1k views (참여율 정규화)")
    lines.append("- 인식(Perception): 상위 댓글의 평균/중앙 좋아요 (약한 긍정 반응 프록시)")
    lines.append("- SoV 최신 월: 조회수/영상/좋아요/댓글 점유율(%) 스냅샷")
    lines.append("")

    lines.append("### 관심도 (Interest)")
    lines.append(df_to_md(res.get("interest")))
    lines.append("")

    lines.append("### 선호도 (Preference)")
    lines.append(df_to_md(res.get("preference")))
    lines.append("")

    lines.append("### 인식 (Perception) — 댓글 반응 프록시")
    lines.append(df_to_md(res.get("perception")))
    lines.append("")

    lines.append("### 최신 월 SoV (%)")
    lines.append(df_to_md(res.get("sov_latest")))
    lines.append("")

    with open(REPORT_MD, "a", encoding="utf-8") as f:
        f.write("\n" + "\n".join(lines) + "\n")


def main():
    videos_df = load_csv(VIDEOS_CSV)
    comments_df = load_csv(COMMENTS_CSV)
    sov_df = load_csv(SOV_CSV)
    res = compute_brand_proxies(videos_df, comments_df, sov_df)
    append_report(res)
    print(f"Appended brand comparison to {REPORT_MD}")


if __name__ == "__main__":
    main()


