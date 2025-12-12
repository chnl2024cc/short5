package com.short5.service;

import com.short5.dto.UserProfileResponse;
import com.short5.dto.VideoResponse;
import com.short5.entity.User;
import com.short5.entity.Video;
import com.short5.entity.Vote;
import com.short5.repository.UserRepository;
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
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    
    @Mock
    private UserRepository userRepository;
    
    @Mock
    private VideoRepository videoRepository;
    
    @Mock
    private VoteRepository voteRepository;
    
    @Mock
    private ViewRepository viewRepository;
    
    @InjectMocks
    private UserService userService;
    
    private User testUser;
    private UUID testUserId;
    private Video testVideo;
    
    @BeforeEach
    void setUp() {
        testUserId = UUID.randomUUID();
        testUser = User.builder()
                .id(testUserId)
                .username("testuser")
                .email("test@example.com")
                .passwordHash("hashed_password")
                .isAdmin(false)
                .isActive(true)
                .createdAt(OffsetDateTime.now())
                .build();
        
        UUID videoId = UUID.randomUUID();
        testVideo = Video.builder()
                .id(videoId)
                .userId(testUserId)
                .title("Test Video")
                .status(Video.VideoStatus.READY)
                .urlMp4("http://example.com/video.mp4")
                .user(testUser)
                .createdAt(OffsetDateTime.now())
                .build();
    }
    
    @Test
    void shouldGetCurrentUserProfile() {
        // Given
        when(userRepository.findById(testUserId)).thenReturn(Optional.of(testUser));
        when(videoRepository.countByUserId(testUserId)).thenReturn(5L);
        when(videoRepository.findByUserIdOrderByCreatedAtDesc(testUserId))
                .thenReturn(List.of(testVideo));
        when(voteRepository.countByVideoIdAndDirection(any(UUID.class), any(Vote.VoteDirection.class)))
                .thenReturn(10L);
        when(viewRepository.countByVideoId(any(UUID.class))).thenReturn(100L);
        
        // When
        UserProfileResponse response = userService.getCurrentUserProfile(testUserId);
        
        // Then
        assertThat(response).isNotNull();
        assertThat(response.getId()).isEqualTo(testUserId.toString());
        assertThat(response.getUsername()).isEqualTo("testuser");
        assertThat(response.getEmail()).isEqualTo("test@example.com");
        assertThat(response.getStats()).isNotNull();
        assertThat(response.getStats().getVideosUploaded()).isEqualTo(5L);
        
        verify(userRepository).findById(testUserId);
        verify(videoRepository).countByUserId(testUserId);
    }
    
    @Test
    void shouldGetUserVideos() {
        // Given
        Pageable pageable = PageRequest.of(0, 20);
        Page<Video> emptyPage = new PageImpl<>(List.of(), pageable, 0);
        when(videoRepository.findByUserIdOrderByCreatedAtDesc(eq(testUserId), any(Pageable.class)))
                .thenReturn(emptyPage);
        
        // When
        List<VideoResponse> videos = userService.getUserVideos(testUserId, null, 20);
        
        // Then
        assertThat(videos).isNotNull();
        verify(videoRepository).findByUserIdOrderByCreatedAtDesc(eq(testUserId), any(Pageable.class));
    }
    
    @Test
    void shouldGetLikedVideos() {
        // Given
        UUID likedVideoId = UUID.randomUUID();
        when(voteRepository.findVideoIdsByUserIdAndDirection(testUserId, Vote.VoteDirection.LIKE))
                .thenReturn(List.of(likedVideoId));
        when(videoRepository.findById(likedVideoId)).thenReturn(Optional.of(testVideo));
        when(voteRepository.countByVideoIdAndDirection(any(UUID.class), any(Vote.VoteDirection.class)))
                .thenReturn(5L);
        when(viewRepository.countByVideoId(any(UUID.class))).thenReturn(50L);
        
        // When
        List<VideoResponse> likedVideos = userService.getLikedVideos(testUserId, null, 20);
        
        // Then
        assertThat(likedVideos).isNotNull();
        verify(voteRepository).findVideoIdsByUserIdAndDirection(testUserId, Vote.VoteDirection.LIKE);
    }
    
    @Test
    void shouldReturnEmptyListWhenNoLikedVideos() {
        // Given
        when(voteRepository.findVideoIdsByUserIdAndDirection(testUserId, Vote.VoteDirection.LIKE))
                .thenReturn(List.of());
        
        // When
        List<VideoResponse> likedVideos = userService.getLikedVideos(testUserId, null, 20);
        
        // Then
        assertThat(likedVideos).isEmpty();
    }
}

