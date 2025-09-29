import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
FIG_DIR = os.path.join(ROOT_DIR, "figures")
REPORT_MD = os.path.join(ROOT_DIR, "ANALYSIS.md")

VIDEOS_CSV = os.path.join(DATA_DIR, "youtube_videos.csv")
COMMENTS_CSV = os.path.join(DATA_DIR, "youtube_comments.csv")
SOV_CSV = os.path.join(DATA_DIR, "youtube_monthly_sov.csv")


def load_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8-sig")


def ensure_fig_dir():
    os.makedirs(FIG_DIR, exist_ok=True)


def plot_interest(videos_df: pd.DataFrame) -> str:
    if videos_df.empty:
        return ""
    df = videos_df.copy()
    df["view_count"] = pd.to_numeric(df["view_count"], errors="coerce").fillna(0)
    agg = df.groupby("brand", as_index=False).agg(videos=("video_id", "nunique"), views=("view_count", "sum"))
    agg = agg.sort_values("views", ascending=False)

    plt.figure(figsize=(7, 4))
    sns.barplot(data=agg, x="brand", y="views", palette="Blues_d")
    plt.title("관심도(Interest): 브랜드별 총 조회수")
    plt.ylabel("총 조회수")
    plt.xlabel("")
    plt.tight_layout()
    path = os.path.join(FIG_DIR, "interest_views.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def plot_preference(videos_df: pd.DataFrame) -> str:
    if videos_df.empty:
        return ""
    df = videos_df.copy()
    for col in ["view_count", "like_count", "comment_count"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    agg = df.groupby("brand", as_index=False).agg(views=("view_count", "sum"), likes=("like_count", "sum"), comments=("comment_count", "sum"))
    agg["likes_per_1k_views"] = (agg["likes"] / agg["views"].replace(0, pd.NA) * 1000).fillna(0)
    agg["comments_per_1k_views"] = (agg["comments"] / agg["views"].replace(0, pd.NA) * 1000).fillna(0)
    agg = agg.melt(id_vars=["brand"], value_vars=["likes_per_1k_views", "comments_per_1k_views"], var_name="metric", value_name="value")

    plt.figure(figsize=(7, 4))
    sns.barplot(data=agg, x="brand", y="value", hue="metric", palette="Set2")
    plt.title("선호도(Preference): 1k뷰당 좋아요/댓글")
    plt.ylabel("값")
    plt.xlabel("")
    plt.legend(title="지표")
    plt.tight_layout()
    path = os.path.join(FIG_DIR, "preference_rates.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def plot_perception(comments_df: pd.DataFrame, videos_df: pd.DataFrame) -> str:
    if comments_df.empty:
        return ""
    df = comments_df.copy()
    df["like_count"] = pd.to_numeric(df.get("like_count", 0), errors="coerce").fillna(0)
    if "brand" not in df.columns and not videos_df.empty:
        df = df.merge(videos_df[["video_id", "brand"]], how="left", on="video_id")
    if "brand" not in df.columns:
        return ""
    agg = df.groupby("brand", as_index=False).agg(avg_comment_likes=("like_count", "mean"))

    plt.figure(figsize=(7, 4))
    sns.barplot(data=agg, x="brand", y="avg_comment_likes", palette="OrRd")
    plt.title("인식(Perception): 상위 댓글 평균 좋아요")
    plt.ylabel("평균 좋아요")
    plt.xlabel("")
    plt.tight_layout()
    path = os.path.join(FIG_DIR, "perception_comment_likes.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def plot_sov_time(sov_df: pd.DataFrame) -> str:
    if sov_df.empty:
        return ""
    df = sov_df.copy()
    df["month"] = pd.to_datetime(df["month"], errors="coerce")
    # Use views share as main line metric
    plt.figure(figsize=(8, 4))
    for brand, g in df.groupby("brand"):
        sns.lineplot(data=g.sort_values("month"), x="month", y="sov_views", label=brand)
    plt.title("월별 SoV(조회수)")
    plt.ylabel("점유율")
    plt.xlabel("월")
    plt.tight_layout()
    path = os.path.join(FIG_DIR, "sov_views_over_time.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def append_to_report(fig_paths: dict):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("## 시각화 결과")
    lines.append(f"- 생성시각: {ts}")
    lines.append("")

    if fig_paths.get("interest"):
        lines.append("### 관심도(Interest): 총 조회수")
        lines.append(f"![interest]({os.path.relpath(fig_paths['interest'], ROOT_DIR).replace('\\', '/')})")
        lines.append("- 조회수가 높을수록 더 넓은 도달과 관심을 의미합니다.")
        lines.append("")

    if fig_paths.get("preference"):
        lines.append("### 선호도(Preference): 1k뷰당 좋아요/댓글")
        lines.append(f"![preference]({os.path.relpath(fig_paths['preference'], ROOT_DIR).replace('\\', '/')})")
        lines.append("- 같은 조회수 대비 높은 좋아요/댓글은 더 강한 선호/참여를 시사합니다.")
        lines.append("")

    if fig_paths.get("perception"):
        lines.append("### 인식(Perception): 상위 댓글 평균 좋아요")
        lines.append(f"![perception]({os.path.relpath(fig_paths['perception'], ROOT_DIR).replace('\\', '/')})")
        lines.append("- 평균 좋아요가 높을수록 긍정적 반응 경향으로 해석할 수 있습니다(약한 프록시).")
        lines.append("")

    if fig_paths.get("sov_time"):
        lines.append("### 월별 SoV(조회수)")
        lines.append(f"![sov]({os.path.relpath(fig_paths['sov_time'], ROOT_DIR).replace('\\', '/')})")
        lines.append("- 월별 조회수 점유율 흐름으로 상대적 모멘텀을 파악합니다.")
        lines.append("")

    with open(REPORT_MD, "a", encoding="utf-8") as f:
        f.write("\n" + "\n".join(lines) + "\n")


def main():
    ensure_fig_dir()
    videos_df = load_csv(VIDEOS_CSV)
    comments_df = load_csv(COMMENTS_CSV)
    sov_df = load_csv(SOV_CSV)

    fig_paths = {
        "interest": plot_interest(videos_df),
        "preference": plot_preference(videos_df),
        "perception": plot_perception(comments_df, videos_df),
        "sov_time": plot_sov_time(sov_df),
    }

    append_to_report(fig_paths)
    print("Figures generated and appended to ANALYSIS.md")


if __name__ == "__main__":
    main()


