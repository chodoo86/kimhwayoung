# Power BI 대시보드 구축 가이드

## "콘텐츠 마케팅의 힘: 어떤 영상이 브랜드 인지도를 높이는가?"

---

## 📋 목차

1. [데이터 준비 및 가져오기](#1-데이터-준비-및-가져오기)
2. [데이터 모델링](#2-데이터-모델링)
3. [DAX 측정값 생성](#3-dax-측정값-생성)
4. [페이지 1: 콘텐츠 성과 분석](#4-페이지-1-콘텐츠-성과-분석)
5. [페이지 2: 바이럴 콘텐츠 탐지](#5-페이지-2-바이럴-콘텐츠-탐지)
6. [페이지 3: 브랜드별 콘텐츠 전략](#6-페이지-3-브랜드별-콘텐츠-전략)
7. [공통 요소 및 필터링](#7-공통-요소-및-필터링)
8. [시각화 최적화 팁](#8-시각화-최적화-팁)

---

## 1. 데이터 준비 및 가져오기

### 1.1 Excel 파일 가져오기

1. **Power BI Desktop** 실행
2. **홈** 탭 → **데이터 가져오기** → **Excel 통합 문서**
3. `powerbi_youtube_data.xlsx` 파일 선택
4. **네비게이터**에서 다음 시트 선택:
   - ✅ `videos` (74개 영상 데이터)
   - ✅ `comments` (17,400개 댓글 데이터)
   - ✅ `monthly_sov` (31개 월별 SoV 데이터)
   - ✅ `brand_summary` (브랜드별 요약 데이터)

### 1.2 데이터 로드

- 각 테이블에서 **로드** 버튼 클릭
- 모든 테이블이 **필드** 패널에 표시되는지 확인

---

## 2. 데이터 모델링

### 2.1 관계 설정 (모델 뷰)

1. **모델** 탭 클릭
2. 다음 관계 생성:

```
comments.video_id → videos.video_id (다대일)
```

**관계 설정 방법:**

- `comments` 테이블의 `video_id` 필드를 `videos` 테이블의 `video_id` 필드로 드래그
- **다대일(Many to One)** 관계 확인
- **활성화** 체크박스 선택

### 2.2 날짜 테이블 생성 (선택사항)

**새 테이블** 생성:

```dax
DateTable = 
CALENDAR(
    DATE(2024,1,1), 
    DATE(2025,12,31)
)
```

**날짜 열 추가:**

```dax
Year = YEAR(DateTable[Date])
Month = MONTH(DateTable[Date])
MonthName = FORMAT(DateTable[Date], "mmm")
Quarter = QUARTER(DateTable[Date])
```

**관계 설정:**

- `DateTable[Date]` ↔ `monthly_sov[month]` (일대다)

---

## 3. DAX 측정값 생성

### 3.1 기본 측정값

**측정값** 패널에서 **새 측정값** 클릭하여 다음 생성:

```dax
# 총 영상 수
Total Videos = DISTINCTCOUNT(videos[video_id])

# 총 조회수
Total Views = SUM(videos[view_count])

# 총 좋아요
Total Likes = SUM(videos[like_count])

# 총 댓글
Total Comments = SUM(videos[comment_count])

# 평균 조회수
Avg Views = AVERAGE(videos[view_count])

# 평균 좋아요
Avg Likes = AVERAGE(videos[like_count])
```

### 3.2 참여율 측정값

```dax
# 참여율 (1k뷰당)
Engagement Rate = 
DIVIDE(
    [Total Likes] + [Total Comments],
    [Total Views]
) * 1000

# 좋아요율 (1k뷰당)
Likes per 1k Views = 
DIVIDE([Total Likes], [Total Views]) * 1000

# 댓글율 (1k뷰당)
Comments per 1k Views = 
DIVIDE([Total Comments], [Total Views]) * 1000
```

### 3.3 바이럴 지수 측정값

```dax
# 바이럴 지수 (조회수 × 참여율)
Viral Score = 
[Total Views] * ([Engagement Rate] / 1000)

# 바이럴 지수 (정규화)
Viral Index = 
DIVIDE(
    [Viral Score],
    MAX(videos[video_id])
)
```

### 3.4 브랜드별 측정값

```dax
# Duolingo 영상 수
Duolingo Videos = 
CALCULATE(
    [Total Videos],
    videos[brand] = "Duolingo"
)

# Speak 영상 수
Speak Videos = 
CALCULATE(
    [Total Videos],
    videos[brand] = "Speak"
)

# 공식 채널 영상 수
Official Videos = 
CALCULATE(
    [Total Videos],
    videos[channel_title] IN ("Duolingo", "스픽 - Speak", "SPEAK")
)

# 크리에이터 채널 영상 수
Creator Videos = 
CALCULATE(
    [Total Videos],
    NOT(videos[channel_title] IN ("Duolingo", "스픽 - Speak", "SPEAK"))
)
```

### 3.5 SoV 측정값

```dax
# 최신 월 SoV (조회수)
Latest SOV Views = 
VAR LatestMonth = CALCULATE(MAX(monthly_sov[month]))
RETURN
CALCULATE(
    AVERAGE(monthly_sov[sov_views]),
    monthly_sov[month] = LatestMonth
)

# SoV 변화율
SOV Change = 
VAR CurrentSOV = [Latest SOV Views]
VAR PreviousSOV = 
    CALCULATE(
        AVERAGE(monthly_sov[sov_views]),
        DATEADD(monthly_sov[month], -1, MONTH)
    )
RETURN
DIVIDE(CurrentSOV - PreviousSOV, PreviousSOV)
```

---

## 4. 페이지 1: 콘텐츠 성과 분석

### 4.1 페이지 설정

- **페이지 이름**: "콘텐츠 성과 분석"
- **페이지 크기**: 16:9 (1920x1080)
- **배경색**: #F8F9FA

### 4.2 KPI 카드 (상단)

**위치**: 상단 중앙, 4개 카드 나란히

#### 카드 1: 총 영상 수

- **시각화**: 카드
- **필드**: `[Total Videos]`
- **서식**:
  - 배경색: #E3F2FD
  - 테두리: 2px, #2196F3
  - 제목: "총 영상 수"
  - 단위: 없음

#### 카드 2: 총 조회수

- **시각화**: 카드
- **필드**: `[Total Views]`
- **서식**:
  - 배경색: #E8F5E8
  - 테두리: 2px, #4CAF50
  - 제목: "총 조회수"
  - 단위: 자동 (천만 단위)

#### 카드 3: 평균 참여율

- **시각화**: 카드
- **필드**: `[Engagement Rate]`
- **서식**:
  - 배경색: #FFF3E0
  - 테두리: 2px, #FF9800
  - 제목: "평균 참여율"
  - 단위: 소수점 2자리

#### 카드 4: 최신 SoV

- **시각화**: 게이지
- **필드**: `[Latest SOV Views]`
- **서식**:
  - 최소값: 0
  - 최대값: 1
  - 배경색: #F3E5F5
  - 테두리: 2px, #9C27B0
  - 제목: "최신 월 SoV"

### 4.3 브랜드별 성과 비교 (중앙 좌측)

**위치**: 중앙 좌측, 2개 차트 세로 배치

#### 차트 1: 브랜드별 조회수

- **시각화**: 막대형 차트 (가로)
- **X축**: `videos[brand]`
- **Y축**: `[Total Views]`
- **범례**: 없음
- **서식**:
  - 색상: 브랜드별 구분 (#FF6B6B, #4ECDC4)
  - 데이터 레이블: 표시
  - 제목: "브랜드별 총 조회수"

#### 차트 2: 브랜드별 참여율

- **시각화**: 막대형 차트 (가로)
- **X축**: `videos[brand]`
- **Y축**: `[Engagement Rate]`
- **범례**: 없음
- **서식**:
  - 색상: 브랜드별 구분 (#FF6B6B, #4ECDC4)
  - 데이터 레이블: 표시
  - 제목: "브랜드별 평균 참여율"

### 4.4 콘텐츠 유형별 성과 (중앙 우측)

**위치**: 중앙 우측, 2개 차트 세로 배치

#### 차트 1: 공식 vs 크리에이터 채널 분포

- **시각화**: 도넛형 차트
- **범례**: 계산된 열 생성

```dax
Channel Type = 
IF(
    videos[channel_title] IN ("Duolingo", "스픽 - Speak", "SPEAK"),
    "공식 채널",
    "크리에이터 채널"
)
```

- **값**: `[Total Videos]`
- **서식**:
  - 색상: #FF9800 (공식), #FFC107 (크리에이터)
  - 제목: "채널 유형별 영상 수"

#### 차트 2: 채널 유형별 평균 성과

- **시각화**: 클러스터형 막대 차트
- **X축**: `[Channel Type]`
- **Y축**: `[Total Views]`, `[Engagement Rate]`
- **범례**: 자동 생성
- **서식**:
  - 제목: "채널 유형별 평균 성과"

### 4.5 시간대별 업로드 패턴 (하단)

**위치**: 하단 전체

#### 히트맵: 시간대별 업로드 분포

- **시각화**: 테이블 (조건부 서식)
- **행**: `videos[brand]`
- **열**: 계산된 열 생성

```dax
Hour Group = 
SWITCH(
    TRUE(),
    videos[hour] IN (0,1,2,3,4,5), "새벽 (0-5시)",
    videos[hour] IN (6,7,8,9,10,11), "오전 (6-11시)",
    videos[hour] IN (12,13,14,15,16,17), "오후 (12-17시)",
    videos[hour] IN (18,19,20,21,22,23), "저녁 (18-23시)"
)
```

- **값**: `[Total Videos]`
- **조건부 서식**: 색상 규모 (진한 파란색 → 진한 빨간색)
- **제목**: "시간대별 업로드 패턴"

---

## 5. 페이지 2: 바이럴 콘텐츠 탐지

### 5.1 페이지 설정

- **페이지 이름**: "바이럴 콘텐츠 탐지"
- **페이지 크기**: 16:9
- **배경색**: #F8F9FA

### 5.2 TOP 바이럴 콘텐츠 (상단)

**위치**: 상단 전체

#### 테이블: 바이럴 지수 TOP 10

- **시각화**: 테이블
- **열**:
  - `videos[brand]`
  - `videos[channel_title]`
  - `videos[title]` (최대 50자)
  - `videos[view_count]`
  - `videos[engagement_rate]`
  - `[Viral Score]`
- **정렬**: `[Viral Score]` 내림차순
- **필터**: 상위 10개
- **서식**:
  - 제목: "바이럴 지수 TOP 10"
  - 행 높이: 40px
  - 열 너비: 자동 조정

### 5.3 성과 지표별 TOP 콘텐츠 (중앙)

**위치**: 중앙, 3개 차트 가로 배치

#### 차트 1: 조회수 TOP 10

- **시각화**: 막대형 차트 (가로)
- **X축**: `videos[title]` (최대 30자)
- **Y축**: `videos[view_count]`
- **범례**: `videos[brand]`
- **필터**: 상위 10개
- **서식**:
  - 색상: 브랜드별 구분
  - 제목: "조회수 TOP 10"

#### 차트 2: 참여율 TOP 10

- **시각화**: 막대형 차트 (가로)
- **X축**: `videos[title]` (최대 30자)
- **Y축**: `[Engagement Rate]`
- **범례**: `videos[brand]`
- **필터**: 상위 10개
- **서식**:
  - 색상: 브랜드별 구분
  - 제목: "참여율 TOP 10"

#### 차트 3: 바이럴 지수 TOP 10

- **시각화**: 막대형 차트 (가로)
- **X축**: `videos[title]` (최대 30자)
- **Y축**: `[Viral Score]`
- **범례**: `videos[brand]`
- **필터**: 상위 10개
- **서식**:
  - 색상: 브랜드별 구분
  - 제목: "바이럴 지수 TOP 10"

### 5.4 성과 지표 상관관계 분석 (하단 좌측)

**위치**: 하단 좌측

#### 산점도: 조회수 vs 참여율

- **시각화**: 산점도
- **X축**: `videos[view_count]`
- **Y축**: `[Engagement Rate]`
- **범례**: `videos[brand]`
- **크기**: `[Viral Score]`
- **도구 설명**: `videos[title]`, `videos[channel_title]`
- **서식**:
  - 제목: "조회수 vs 참여율 상관관계"
  - X축 로그 스케일: 사용

### 5.5 브랜드별 바이럴 성과 (하단 우측)

**위치**: 하단 우측

#### 트리맵: 브랜드별 바이럴 지수 분포

- **시각화**: 트리맵
- **그룹**: `videos[brand]`
- **값**: `[Viral Score]`
- **색상**: `videos[brand]`
- **서식**:
  - 제목: "브랜드별 바이럴 지수 분포"
  - 색상: 브랜드별 구분

---

## 6. 페이지 3: 브랜드별 콘텐츠 전략

### 6.1 페이지 설정

- **페이지 이름**: "브랜드별 콘텐츠 전략"
- **페이지 크기**: 16:9
- **배경색**: #F8F9FA

### 6.2 브랜드별 콘텐츠 DNA (상단)

**위치**: 상단 전체

#### 워드 클라우드: 브랜드별 태그 분석

- **시각화**: 테이블 (태그 빈도)
- **행**: 계산된 열 생성

```dax
Tag List = 
SUBSTITUTE(
    SUBSTITUTE(videos[tags], ",", "|"),
    " ",
    ""
)
```

- **값**: 태그별 카운트
- **서식**:
  - 제목: "브랜드별 콘텐츠 태그 분석"
  - 조건부 서식: 태그 빈도에 따른 색상

### 6.3 Duolingo 전략 분석 (중앙 좌측)

**위치**: 중앙 좌측

#### 차트 1: Duolingo 콘텐츠 유형

- **시각화**: 도넛형 차트
- **범례**: 계산된 열 생성

```dax
Duolingo Content Type = 
IF(
    CONTAINSSTRING(videos[title], "Squid Game") || 
    CONTAINSSTRING(videos[title], "Chess") ||
    CONTAINSSTRING(videos[title], "Super Bowl"),
    "협업 콘텐츠",
    IF(
        CONTAINSSTRING(videos[title], "meme") ||
        CONTAINSSTRING(videos[title], "funny"),
        "밈 콘텐츠",
        "일반 콘텐츠"
    )
)
```

- **값**: `[Total Videos]`
- **필터**: `videos[brand] = "Duolingo"`

#### 차트 2: Duolingo 채널별 성과

- **시각화**: 막대형 차트
- **X축**: `videos[channel_title]`
- **Y축**: `[Total Views]`
- **범례**: 없음
- **필터**: `videos[brand] = "Duolingo"`

### 6.4 Speak 전략 분석 (중앙 우측)

**위치**: 중앙 우측

#### 차트 1: Speak 콘텐츠 유형

- **시각화**: 도넛형 차트
- **범례**: 계산된 열 생성

```dax
Speak Content Type = 
IF(
    CONTAINSSTRING(videos[title], "영어회화") ||
    CONTAINSSTRING(videos[title], "communication"),
    "교육 콘텐츠",
    IF(
        CONTAINSSTRING(videos[title], "롤") ||
        CONTAINSSTRING(videos[title], "게임"),
        "게임 콘텐츠",
        "일반 콘텐츠"
    )
)
```

- **값**: `[Total Views]`
- **필터**: `videos[brand] = "Speak"`

#### 차트 2: Speak 채널별 성과

- **시각화**: 막대형 차트
- **X축**: `videos[channel_title]`
- **Y축**: `[Total Views]`
- **범례**: 없음
- **필터**: `videos[brand] = "Speak"`

### 6.5 콘텐츠 전략 비교 (하단)

**위치**: 하단 전체

#### 테이블: 브랜드별 콘텐츠 전략 요약

- **시각화**: 테이블
- **열**:
  - `videos[brand]`
  - `[Total Videos]`
  - `[Total Views]`
  - `[Engagement Rate]`
  - `[Official Videos]`
  - `[Creator Videos]`
  - `[Viral Score]`
- **그룹화**: `videos[brand]`
- **서식**:
  - 제목: "브랜드별 콘텐츠 전략 요약"
  - 조건부 서식: 수치별 색상 구분

---

## 7. 공통 요소 및 필터링

### 7.1 전역 필터 (모든 페이지)

**위치**: 각 페이지 상단

#### 슬라이서 1: 브랜드 선택

- **시각화**: 슬라이서
- **필드**: `videos[brand]`
- **서식**:
  - 유형: 목록
  - 다중 선택: 허용
  - 기본값: 모든 선택

#### 슬라이서 2: 기간 선택

- **시각화**: 슬라이서
- **필드**: `videos[published_at]`
- **서식**:
  - 유형: 날짜 범위
  - 기본값: 최근 12개월

#### 슬라이서 3: 채널 유형

- **시각화**: 슬라이서
- **필드**: `[Channel Type]`
- **서식**:
  - 유형: 목록
  - 다중 선택: 허용

### 7.2 공통 도구 설명

모든 차트에 다음 도구 설명 추가:

- 브랜드명
- 채널명
- 영상 제목 (간략)
- 조회수
- 참여율
- 바이럴 지수

---

## 8. 시각화 최적화 팁

### 8.1 성능 최적화

1. **데이터 모델**:

   - 불필요한 열 제거
   - 계산된 열보다 측정값 사용
   - 관계 최적화
2. **시각화**:

   - 복잡한 계산은 DAX로 처리
   - 조건부 서식 최소화
   - 대용량 테이블은 페이지네이션 사용

### 8.2 사용자 경험 개선

1. **색상 통일**:

   - Duolingo: #FF6B6B (빨간색 계열)
   - Speak: #4ECDC4 (청록색 계열)
   - 공통: #95A5A6 (회색 계열)
2. **폰트 및 크기**:

   - 제목: 16px, 굵게
   - 데이터 레이블: 12px
   - 축 레이블: 11px
3. **인터랙션**:

   - 크로스 필터링 활성화
   - 하이라이트 모드 설정
   - 드릴스루 기능 추가
