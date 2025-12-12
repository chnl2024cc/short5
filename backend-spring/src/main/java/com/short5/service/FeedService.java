package com.short5.service;

import com.short5.dto.FeedResponse;
import com.short5.dto.VideoResponse;
import com.short5.entity.User;
import com.short5.entity.Video;
import com.short5.entity.Vote;
import com.short5.entity.Vote.VoteDirection;
import com.short5.entity.Video.VideoStatus;
import com.short5.repository.VideoRepository;
import com.short5.repository.VoteRepository;
import com.short5.repository.ViewRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class FeedService {
    
    private final VideoRepository videoRepository;
    private final VoteRepository voteRepository;
    private final ViewRepository viewRepository;
    
    @Transactional(readOnly = true)
    public FeedResponse getFeed(UUID userId, String cursor, int limit) {
        log.info("Getting feed for user: {}, cursor: {}, limit: {}", userId, cursor, limit);
        
        // Get candidate videos (only ready videos with MP4 files)
        Pageable pageable = PageRequest.of(0, limit * 3); // Get 3x limit for scoring
        List<Video> candidates = videoRepository.findByStatusOrderByCreatedAtDesc(VideoStatus.READY, pageable)
                .getContent()
                .stream()
                .filter(video -> video.getUrlMp4() != null && !video.getUrlMp4().isEmpty())
                .collect(Collectors.toList());
        
        // Exclude videos user has liked
        if (userId != null) {
            List<UUID> likedVideoIds = voteRepository.findVideoIdsByUserIdAndDirection(userId, VoteDirection.LIKE);
            candidates = candidates.stream()
                    .filter(video -> !likedVideoIds.contains(video.getId()))
                    .collect(Collectors.toList());
        }
        
        // Apply cursor pagination
        if (cursor != null && !cursor.isEmpty()) {
            try {
                OffsetDateTime cursorTime = OffsetDateTime.parse(cursor);
                candidates = candidates.stream()
                        .filter(video -> video.getCreatedAt().isBefore(cursorTime))
                        .collect(Collectors.toList());
            } catch (Exception e) {
                log.warn("Invalid cursor format: {}", cursor);
            }
        }
        
        if (candidates.isEmpty()) {
            return FeedResponse.builder()
                    .videos(List.of())
                    .nextCursor(null)
                    .hasMore(false)
                    .build();
        }
        
        // Calculate scores and sort
        List<ScoredVideo> scoredVideos = candidates.stream()
                .map(video -> {
                    try {
                        double score = calculateVideoScore(video, userId);
                        return new ScoredVideo(score, video);
                    } catch (Exception e) {
                        log.warn("Error scoring video {}: {}", video.getId(), e.getMessage());
                        return null;
                    }
                })
                .filter(Objects::nonNull)
                .sorted(Comparator.comparing(ScoredVideo::getScore).reversed())
                .limit(limit)
                .collect(Collectors.toList());
        
        // Convert to VideoResponse
        List<VideoResponse> videos = scoredVideos.stream()
                .map(scoredVideo -> convertToVideoResponse(scoredVideo.getVideo()))
                .collect(Collectors.toList());
        
        // Determine next cursor
        String nextCursor = null;
        boolean hasMore = candidates.size() > limit;
        if (hasMore && !videos.isEmpty()) {
            nextCursor = videos.get(videos.size() - 1).getCreatedAt().toString();
        }
        
        return FeedResponse.builder()
                .videos(videos)
                .nextCursor(nextCursor)
                .hasMore(hasMore)
                .build();
    }
    
    private double calculateVideoScore(Video video, UUID userId) {
        double score = 0.5; // Base score
        
        if (userId == null) {
            // New user: use popularity only
            long likes = voteRepository.countByVideoIdAndDirection(video.getId(), VoteDirection.LIKE);
            long views = viewRepository.countByVideoId(video.getId());
            
            double popularity = views > 0 ? (double) likes / views * Math.min(views, 100) / 100 : 0;
            score = 0.3 + (popularity * 0.7);
            
            // Recency boost
            long daysOld = java.time.temporal.ChronoUnit.DAYS.between(video.getCreatedAt(), OffsetDateTime.now());
            double recency = Math.max(0, 1.0 - (daysOld / 30.0));
            score += recency * 0.2;
            
            return score;
        }
        
        // Get user's liked/not-liked creators
        List<UUID> likedCreatorIds = voteRepository.findVideoIdsByUserIdAndDirection(userId, VoteDirection.LIKE)
                .stream()
                .map(videoId -> {
                    Optional<Video> v = videoRepository.findById(videoId);
                    return v.map(Video::getUserId).orElse(null);
                })
                .filter(Objects::nonNull)
                .distinct()
                .collect(Collectors.toList());
        
        List<UUID> notLikedCreatorIds = voteRepository.findVideoIdsByUserIdAndDirection(userId, VoteDirection.NOT_LIKE)
                .stream()
                .map(videoId -> {
                    Optional<Video> v = videoRepository.findById(videoId);
                    return v.map(Video::getUserId).orElse(null);
                })
                .filter(Objects::nonNull)
                .distinct()
                .collect(Collectors.toList());
        
        // Creator-based score (40% weight)
        if (likedCreatorIds.contains(video.getUserId())) {
            long creatorLikes = voteRepository.findVideoIdsByUserIdAndDirection(userId, VoteDirection.LIKE)
                    .stream()
                    .map(videoRepository::findById)
                    .filter(Optional::isPresent)
                    .map(Optional::get)
                    .filter(v -> v.getUserId().equals(video.getUserId()))
                    .count();
            double creatorScore = 1.0 + Math.min(creatorLikes / 10.0, 1.0);
            score += creatorScore * 0.4;
        } else if (notLikedCreatorIds.contains(video.getUserId())) {
            score *= 0.1; // Heavy penalty
        } else {
            score += 0.5 * 0.4; // Neutral
        }
        
        // Popularity score (30% weight)
        long likes = voteRepository.countByVideoIdAndDirection(video.getId(), VoteDirection.LIKE);
        long views = viewRepository.countByVideoId(video.getId());
        double popularity = views > 0 ? (double) likes / views * Math.min(views, 100) / 100 : 0;
        score += popularity * 0.3;
        
        // Recency score (20% weight)
        long daysOld = java.time.temporal.ChronoUnit.DAYS.between(video.getCreatedAt(), OffsetDateTime.now());
        double recency = Math.max(0, 1.0 - (daysOld / 30.0));
        score += recency * 0.2;
        
        return score;
    }
    
    private VideoResponse convertToVideoResponse(Video video) {
        User user = video.getUser();
        if (user == null) {
            // This shouldn't happen if we properly load the user
            log.warn("User not loaded for video {}", video.getId());
            return null;
        }
        
        long likes = voteRepository.countByVideoIdAndDirection(video.getId(), VoteDirection.LIKE);
        long notLikes = voteRepository.countByVideoIdAndDirection(video.getId(), VoteDirection.NOT_LIKE);
        long views = viewRepository.countByVideoId(video.getId());
        
        return VideoResponse.builder()
                .id(video.getId().toString())
                .title(video.getTitle())
                .description(video.getDescription())
                .status(video.getStatus().name())
                .thumbnail(video.getThumbnail())
                .urlMp4(video.getUrlMp4())
                .durationSeconds(video.getDurationSeconds())
                .errorReason(video.getErrorReason())
                .user(VideoResponse.UserBasic.builder()
                        .id(user.getId().toString())
                        .username(user.getUsername())
                        .build())
                .stats(VideoResponse.VideoStats.builder()
                        .likes(likes)
                        .notLikes(notLikes)
                        .views(views)
                        .build())
                .createdAt(video.getCreatedAt())
                .build();
    }
    
    private static class ScoredVideo {
        private final double score;
        private final Video video;
        
        public ScoredVideo(double score, Video video) {
            this.score = score;
            this.video = video;
        }
        
        public double getScore() {
            return score;
        }
        
        public Video getVideo() {
            return video;
        }
    }
}

