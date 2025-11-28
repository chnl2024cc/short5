# Recommendation Algorithm Specification

## Overview
The recommendation algorithm personalizes the video feed based on user interactions (likes/not-likes) to show relevant content while reducing unwanted videos.

## Core Principles
1. **Likes boost similar content** - Videos similar to liked content appear more frequently
2. **Not-likes reduce similar content** - Videos similar to not-liked content appear less frequently
3. **Fallback for new users** - Popular/recent videos for users with no interaction history
4. **Diversity** - Prevent filter bubbles by mixing content types

---

## Similarity Factors

### 1. Creator-Based Similarity (Weight: 40%)
- If user likes videos from Creator A, boost other videos from Creator A
- If user not-likes videos from Creator A, reduce other videos from Creator A

### 2. Content-Based Similarity (Weight: 30%)
- **Title/Description Keywords** - Simple keyword matching (TF-IDF)
- **Video Length** - Similar duration preferences
- **Upload Time** - Recent vs older content preferences

### 3. Engagement-Based Similarity (Weight: 20%)
- Videos with similar like/view ratios
- Videos with similar watch time patterns

### 4. Temporal Factors (Weight: 10%)
- Recent uploads get slight boost
- Trending videos (high engagement rate) get boost

---

## Scoring Formula

For each video candidate:

```
score = (
    creator_score * 0.4 +
    content_score * 0.3 +
    engagement_score * 0.2 +
    temporal_score * 0.1
) * diversity_multiplier
```

### Creator Score
```
if video.creator_id in liked_creators:
    creator_score = 1.0 + (likes_from_creator / total_likes) * 2.0
elif video.creator_id in not_liked_creators:
    creator_score = 0.1  # Heavy penalty
else:
    creator_score = 0.5  # Neutral
```

### Content Score
```
content_score = keyword_match_score * 0.6 + length_similarity * 0.4

keyword_match_score = count(matching_keywords) / max_keywords_in_liked_videos
length_similarity = 1.0 - abs(video.length - avg_liked_length) / max_length
```

### Engagement Score
```
engagement_score = (
    (video.likes / video.views) * 0.5 +
    (video.avg_watch_time / video.length) * 0.5
)
```

### Temporal Score
```
temporal_score = (
    recency_boost * 0.6 +  # Newer = higher
    trend_boost * 0.4       # High engagement rate = higher
)

recency_boost = 1.0 - (days_since_upload / 30)  # Decay over 30 days
trend_boost = min(video.engagement_rate / 0.1, 1.0)  # Cap at 10% engagement
```

### Diversity Multiplier
```
# Prevent showing too many videos from same creator
if creator_videos_in_feed >= 2:
    diversity_multiplier = 0.7
else:
    diversity_multiplier = 1.0
```

---

## Feed Generation Algorithm

### Step 1: Candidate Selection
1. Get all videos with `status = 'ready'`
2. Exclude videos user has already voted on
3. Exclude videos user has already viewed (optional, for MVP show all)

### Step 2: Scoring
1. Calculate score for each candidate using formula above
2. Sort by score (descending)

### Step 3: Diversity Injection
1. Every 5th video, inject a random popular video (score > 0.5)
2. This prevents filter bubbles

### Step 4: Pagination
1. Return top N videos (default: 10)
2. Use cursor-based pagination (last video ID + score)

---

## New User Fallback

For users with < 5 interactions:
```
score = (
    popularity_score * 0.6 +  # Likes/views ratio
    recency_score * 0.4        # Recent uploads
)
```

Popularity Score:
```
popularity_score = (video.likes / video.views) * log(video.views + 1)
```

---

## Implementation Notes

### MVP Simplification
For MVP, use simplified version:
1. **Creator-based only** - Boost/reduce based on creator likes
2. **Popularity fallback** - For new users, show popular videos
3. **No content analysis** - Skip keyword matching initially

### Database Queries
```sql
-- Get liked creators
SELECT DISTINCT v.user_id, COUNT(*) as like_count
FROM votes v
JOIN videos vid ON v.video_id = vid.id
WHERE v.user_id = ? AND v.direction = 'like'
GROUP BY v.user_id

-- Get not-liked creators
SELECT DISTINCT v.user_id
FROM votes v
JOIN videos vid ON v.video_id = vid.id
WHERE v.user_id = ? AND v.direction = 'not_like'
```

### Caching Strategy
- Cache user's liked/not-liked creators (TTL: 5 minutes)
- Cache popular videos list (TTL: 1 hour)
- Cache feed results per user (TTL: 2 minutes)

---

## Future Enhancements
1. **Machine Learning** - Train model on user behavior
2. **Collaborative Filtering** - "Users who liked X also liked Y"
3. **Content Embeddings** - Video frame analysis for visual similarity
4. **Category/Tags** - Explicit categorization system
5. **Watch Time Analysis** - Boost videos with high completion rates

