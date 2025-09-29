import os
from datetime import datetime
import pandas as pd


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
VIDEOS_CSV = os.path.join(DATA_DIR, "youtube_videos.csv")
COMMENTS_CSV = os.path.join(DATA_DIR, "youtube_comments.csv")
SOV_CSV = os.path.join(DATA_DIR, "youtube_monthly_sov.csv")
REPORT_MD = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ANALYSIS.md")


def load_csv_safe(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    # utf-8-sig for compatibility
    return pd.read_csv(path, encoding="utf-8-sig")


def compute_aggregates(videos_df: pd.DataFrame, comments_df: pd.DataFrame) -> dict:
    results = {}
    if videos_df.empty:
        return results

    # Ensure types
    for col in ["view_count", "like_count", "comment_count"]:
        if col in videos_df.columns:
            videos_df[col] = pd.to_numeric(videos_df[col], errors="coerce").fillna(0).astype(int)

    # Per brand aggregates
    brand_grp = videos_df.groupby("brand", as_index=False).agg(
        videos=("video_id", "nunique"),
        views=("view_count", "sum"),
        likes=("like_count", "sum"),
        comments=("comment_count", "sum"),
    )

    # Per brand averages per video
    brand_grp["avg_views_per_video"] = (brand_grp["views"] / brand_grp["videos"]).round(2)
    brand_grp["avg_likes_per_video"] = (brand_grp["likes"] / brand_grp["videos"]).round(2)
    brand_grp["avg_comments_per_video"] = (brand_grp["comments"] / brand_grp["videos"]).round(2)

    # Top channels by number of videos per brand
    top_channels = (
        videos_df.groupby(["brand", "channel_title"], as_index=False)["video_id"].nunique()
        .rename(columns={"video_id": "video_count"})
        .sort_values(["brand", "video_count"], ascending=[True, False])
    )

    # Comments per brand (from comments_df joined to brand)
    comments_by_brand = pd.DataFrame()
    if not comments_df.empty and "brand" in comments_df.columns:
        comments_by_brand = comments_df.groupby("brand", as_index=False).size().rename(columns={"size": "total_top_level_comments"})

    results["brand_aggregates"] = brand_grp
    results["top_channels"] = top_channels
    results["comments_by_brand"] = comments_by_brand
    return results


def summarize_latest_month_sov(sov_df: pd.DataFrame) -> pd.DataFrame:
    if sov_df.empty or "month" not in sov_df.columns:
        return pd.DataFrame()
    # Parse month
    sov_df["month"] = pd.to_datetime(sov_df["month"], errors="coerce")
    latest_month = sov_df["month"].max()
    if pd.isna(latest_month):
        return pd.DataFrame()
    latest = sov_df[sov_df["month"] == latest_month].copy()
    return latest.sort_values(["sov_views", "sov_videos"], ascending=False)


def df_to_md_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "(no data)"
    df_show = df.head(max_rows)
    # Build Markdown table manually to avoid reliance on df.to_markdown
    headers = list(df_show.columns)
    lines = ["| " + " | ".join(map(str, headers)) + " |",
             "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in df_show.iterrows():
        cells = [str(row[h]) for h in headers]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main():
    videos_df = load_csv_safe(VIDEOS_CSV)
    comments_df = load_csv_safe(COMMENTS_CSV)
    sov_df = load_csv_safe(SOV_CSV)

    # If comments lack brand, try merge from videos
    if not comments_df.empty and "brand" not in comments_df.columns and not videos_df.empty:
        comments_df = comments_df.merge(videos_df[["video_id", "brand"]], how="left", on="video_id")

    aggs = compute_aggregates(videos_df, comments_df)
    latest_sov = summarize_latest_month_sov(sov_df)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append(f"## YouTube 수집 데이터 분석\n")
    lines.append(f"- 생성시각: {ts}\n")
    lines.append("")

    # 방법
    lines.append("### 분석 방법")
    lines.append("- videos: 브랜드별 영상수, 조회수/좋아요/댓글 합계 및 평균 산출")
    lines.append("- comments: 브랜드별 상위 댓글 수 합계")
    lines.append("- SoV: 월별 점유율 테이블에서 최신 월을 요약")
    lines.append("")

    # 결과: brand aggregates
    lines.append("### 브랜드별 핵심 지표")
    lines.append(df_to_md_table(aggs.get("brand_aggregates", pd.DataFrame())))
    lines.append("")

    # 결과: comments per brand
    lines.append("### 브랜드별 상위 댓글 수")
    lines.append(df_to_md_table(aggs.get("comments_by_brand", pd.DataFrame())))
    lines.append("")

    # 결과: top channels
    lines.append("### 브랜드별 영상 업로드 상위 채널")
    lines.append(df_to_md_table(aggs.get("top_channels", pd.DataFrame()), max_rows=30))
    lines.append("")

    # 결과: latest SoV
    lines.append("### 최신 월 SoV 요약")
    lines.append(df_to_md_table(latest_sov))
    lines.append("")

    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Report written to {REPORT_MD}")


if __name__ == "__main__":
    main()


