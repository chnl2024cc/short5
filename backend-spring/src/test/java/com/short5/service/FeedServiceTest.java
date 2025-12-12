package com.short5.service;

import com.short5.dto.FeedResponse;
import com.short5.entity.User;
import com.short5.entity.Video;
import com.short5.entity.Vote;
import com.short5.entity.Video.VideoStatus;
import com.short5.entity.Vote.VoteDirection;
import com.short5.repository.VideoRepository;
import com.short5.repository.VoteRepository;
import com.short5.repository.ViewRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class FeedServiceTest {
    
    @Mock
    private VideoRepository videoRepository;
    
    @Mock
    private VoteRepository voteRepository;
    
    @Mock
    private ViewRepository viewRepository;
    
    @InjectMocks
    private FeedService feedService;
    
    private User testUser;
    private Video testVideo;
    private UUID testUserId;
    private UUID testVideoId;
    
    @BeforeEach
    void setUp() {
        testUserId = UUID.randomUUID();
        testUser = User.builder()
                .id(testUserId)
                .username("testuser")
                .build();
        
        testVideoId = UUID.randomUUID();
        testVideo = Video.builder()
                .id(testVideoId)
                .userId(testUserId)
                .title("Test Video")
                .status(VideoStatus.READY)
                .urlMp4("http://example.com/video.mp4")
                .user(testUser)
                .createdAt(OffsetDateTime.now())
                .build();
    }
    
    @Test
    void shouldGetFeedForAuthenticatedUser() {
        // Given
        Pageable pageable = PageRequest.of(0, 30);
        Page<Video> videoPage = new PageImpl<>(List.of(testVideo), pageable, 1);
        
        when(videoRepository.findByStatusOrderByCreatedAtDesc(VideoStatus.READY, pageable))
                .thenReturn(videoPage);
        when(voteRepository.findVideoIdsByUserIdAndDirection(testUserId, VoteDirection.LIKE))
                .thenReturn(List.of());
        when(voteRepository.countByVideoIdAndDirection(any(), any())).thenReturn(0L);
        when(viewRepository.countByVideoId(any())).thenReturn(0L);
        
        // When
        FeedResponse response = feedService.getFeed(testUserId, null, 10);
        
        // Then
        assertThat(response).isNotNull();
        assertThat(response.getVideos()).isNotEmpty();
        verify(videoRepository).findByStatusOrderByCreatedAtDesc(VideoStatus.READY, pageable);
    }
    
    @Test
    void shouldGetFeedForAnonymousUser() {
        // Given
        Pageable pageable = PageRequest.of(0, 30);
        Page<Video> videoPage = new PageImpl<>(List.of(testVideo), pageable, 1);
        
        when(videoRepository.findByStatusOrderByCreatedAtDesc(VideoStatus.READY, pageable))
                .thenReturn(videoPage);
        when(voteRepository.countByVideoIdAndDirection(any(), any())).thenReturn(5L);
        when(viewRepository.countByVideoId(any())).thenReturn(100L);
        
        // When
        FeedResponse response = feedService.getFeed(null, null, 10);
        
        // Then
        assertThat(response).isNotNull();
        assertThat(response.getVideos()).isNotEmpty();
    }
    
    @Test
    void shouldExcludeLikedVideosFromFeed() {
        // Given
        UUID likedVideoId = UUID.randomUUID();
        Video likedVideo = Video.builder()
                .id(likedVideoId)
                .userId(testUserId)
                .status(VideoStatus.READY)
                .urlMp4("http://example.com/liked.mp4")
                .user(testUser)
                .createdAt(OffsetDateTime.now())
                .build();
        
        Pageable pageable = PageRequest.of(0, 30);
        Page<Video> videoPage = new PageImpl<>(List.of(testVideo, likedVideo), pageable, 2);
        
        when(videoRepository.findByStatusOrderByCreatedAtDesc(VideoStatus.READY, pageable))
                .thenReturn(videoPage);
        when(voteRepository.findVideoIdsByUserIdAndDirection(testUserId, VoteDirection.LIKE))
                .thenReturn(List.of(likedVideoId));
        when(voteRepository.countByVideoIdAndDirection(any(), any())).thenReturn(0L);
        when(viewRepository.countByVideoId(any())).thenReturn(0L);
        
        // When
        FeedResponse response = feedService.getFeed(testUserId, null, 10);
        
        // Then
        assertThat(response).isNotNull();
        assertThat(response.getVideos()).hasSize(1);
        assertThat(response.getVideos().get(0).getId()).isEqualTo(testVideoId.toString());
    }
    
    @Test
    void shouldReturnEmptyFeedWhenNoVideos() {
        // Given
        Pageable pageable = PageRequest.of(0, 30);
        Page<Video> emptyPage = new PageImpl<>(List.of(), pageable, 0);
        
        when(videoRepository.findByStatusOrderByCreatedAtDesc(VideoStatus.READY, pageable))
                .thenReturn(emptyPage);
        
        // When
        FeedResponse response = feedService.getFeed(null, null, 10);
        
        // Then
        assertThat(response).isNotNull();
        assertThat(response.getVideos()).isEmpty();
        assertThat(response.getHasMore()).isFalse();
    }
}

