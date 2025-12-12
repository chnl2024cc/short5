package com.short5.service;

import com.short5.dto.UserProfileResponse;
import com.short5.dto.VideoResponse;
import com.short5.entity.User;
import com.short5.entity.Video;
import com.short5.entity.Vote;
import com.short5.entity.View;
import com.short5.entity.Vote.VoteDirection;
import com.short5.repository.UserRepository;
import com.short5.repository.VideoRepository;
import com.short5.repository.VoteRepository;
import com.short5.repository.ViewRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class UserService {
    
    private final UserRepository userRepository;
    private final VideoRepository videoRepository;
    private final VoteRepository voteRepository;
    private final ViewRepository viewRepository;
    
    @Transactional(readOnly = true)
    public UserProfileResponse getCurrentUserProfile(UUID userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));
        
        // Get user stats
        long videosUploaded = videoRepository.countByUserId(userId);
        
        // Count likes received on user's videos
        long totalLikesReceived = videoRepository.findByUserIdOrderByCreatedAtDesc(userId).stream()
                .mapToLong(video -> voteRepository.countByVideoIdAndDirection(video.getId(), VoteDirection.LIKE))
                .sum();
        
        // Count views on user's videos
        long totalViews = videoRepository.findByUserIdOrderByCreatedAtDesc(userId).stream()
                .mapToLong(video -> viewRepository.countByVideoId(video.getId()))
                .sum();
        
        return UserProfileResponse.builder()
                .id(user.getId().toString())
                .username(user.getUsername())
                .email(user.getEmail())
                .isAdmin(user.getIsAdmin())
                .createdAt(user.getCreatedAt())
                .stats(UserProfileResponse.UserStats.builder()
                        .videosUploaded(videosUploaded)
                        .totalLikesReceived(totalLikesReceived)
                        .totalViews(totalViews)
                        .build())
                .build();
    }
    
    @Transactional(readOnly = true)
    public List<VideoResponse> getUserVideos(UUID userId, String cursor, int limit) {
        Pageable pageable = PageRequest.of(0, Math.min(limit, 100));
        Page<Video> videoPage;
        
        if (cursor != null && !cursor.isEmpty()) {
            try {
                OffsetDateTime cursorTime = OffsetDateTime.parse(cursor);
                // Note: This is simplified - in production, you'd use a proper cursor-based query
                videoPage = videoRepository.findByUserIdOrderByCreatedAtDesc(userId, pageable);
            } catch (Exception e) {
                log.warn("Invalid cursor format: {}", cursor);
                videoPage = videoRepository.findByUserIdOrderByCreatedAtDesc(userId, pageable);
            }
        } else {
            videoPage = videoRepository.findByUserIdOrderByCreatedAtDesc(userId, pageable);
        }
        
        return videoPage.getContent().stream()
                .map(this::convertToVideoResponse)
                .collect(Collectors.toList());
    }
    
    @Transactional(readOnly = true)
    public List<VideoResponse> getLikedVideos(UUID userId, String cursor, int limit) {
        // Get video IDs that user has liked
        List<UUID> likedVideoIds = voteRepository.findVideoIdsByUserIdAndDirection(userId, VoteDirection.LIKE);
        
        if (likedVideoIds.isEmpty()) {
            return List.of();
        }
        
        // Get videos
        List<Video> videos = likedVideoIds.stream()
                .map(videoRepository::findById)
                .filter(java.util.Optional::isPresent)
                .map(java.util.Optional::get)
                .limit(Math.min(limit, 100))
                .collect(Collectors.toList());
        
        return videos.stream()
                .map(this::convertToVideoResponse)
                .collect(Collectors.toList());
    }
    
    @Transactional(readOnly = true)
    public Map<String, Object> getPublicUserProfile(UUID userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));
        
        // Get user stats
        long videosUploaded = videoRepository.countByUserId(userId);
        
        // Count likes received on user's videos
        long totalLikesReceived = videoRepository.findByUserIdOrderByCreatedAtDesc(userId).stream()
                .mapToLong(video -> voteRepository.countByVideoIdAndDirection(video.getId(), VoteDirection.LIKE))
                .sum();
        
        // Count views on user's videos
        long totalViews = videoRepository.findByUserIdOrderByCreatedAtDesc(userId).stream()
                .mapToLong(video -> viewRepository.countByVideoId(video.getId()))
                .sum();
        
        Map<String, Object> profile = new HashMap<>();
        profile.put("id", user.getId().toString());
        profile.put("username", user.getUsername());
        profile.put("created_at", user.getCreatedAt().toString());
        profile.put("stats", Map.of(
            "videos_uploaded", videosUploaded,
            "total_likes_received", totalLikesReceived,
            "total_views", totalViews
        ));
        
        return profile;
    }
    
    private VideoResponse convertToVideoResponse(Video video) {
        User user = video.getUser();
        if (user == null) {
            // Load user if not loaded
            user = userRepository.findById(video.getUserId())
                    .orElseThrow(() -> new RuntimeException("User not found for video"));
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
}

