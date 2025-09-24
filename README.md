### YouTube SoV Collector (배달앱: 배달의민족/요기요/쿠팡이츠)

This script collects YouTube videos and top-level comments mentioning the three delivery app brands, then exports:
- videos CSV
- comments CSV
- monthly Share of Voice (SoV) CSV (based on videos/views/likes/comments)

#### 1) Setup
- Python 3.10+
- Install deps:
```
pip install -r requirements.txt
```
- Create `.env`:
```
YOUTUBE_API_KEY=YOUR_API_KEY
PUBLISHED_AFTER=2024-01-01T00:00:00Z
# PUBLISHED_BEFORE=2025-12-31T23:59:59Z
OUTPUT_DIR=data
```

#### 2) Run
```
python scripts/youtube_sov_collect.py
```

Outputs (default `data/`):
- `youtube_videos.csv`
- `youtube_comments.csv`
- `youtube_monthly_sov.csv`

#### Notes
- Only top-level comments are collected (per-video cap configurable).
- Brands searched: 배달의민족, 요기요, 쿠팡이츠. Modify `BRANDS` in `scripts/youtube_sov_collect.py`.
- For SoV we compute monthly shares for videos/views/likes/comments; Power BI can ingest these directly.
