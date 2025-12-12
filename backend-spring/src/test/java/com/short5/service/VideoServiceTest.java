package com.short5.service;

import com.short5.dto.*;
import com.short5.entity.User;
import com.short5.entity.Video;
import com.short5.entity.Vote;
import com.short5.entity.View;
import com.short5.entity.Video.VideoStatus;
import com.short5.entity.Vote.VoteDirection;
import com.short5.repository.*;
import com.short5.entity.UserLikedVideo;
import com.short5.entity.ShareLink;
import com.short5.entity.ShareClick;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.OffsetDateTime;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class VideoServiceTest {
    
    @Mock
    private VideoRepository videoRepository;
    
    @Mock
    private UserRepository userRepository;
    
    @Mock
    private VoteRepository voteRepository;
    
    @Mock
    private ViewRepository viewRepository;
    
    @Mock
    private UserLikedVideoRepository userLikedVideoRepository;
    
    @Mock
    private ShareLinkRepository shareLinkRepository;
    
    @Mock
    private ShareClickRepository shareClickRepository;
    
    @InjectMocks
    private VideoService videoService;
    
    private User testUser;
    private UUID testUserId;
    private Video testVideo;
    private UUID testVideoId;
    
    @BeforeEach
    void setUp() {
        testUserId = UUID.randomUUID();
        testUser = User.builder()
                .id(testUserId)
                .username("testuser")
                .email("test@example.com")
                .build();
        
        testVideoId = UUID.randomUUID();
        testVideo = Video.builder()
                .id(testVideoId)
                .userId(testUserId)
                .title("Test Video")
                .status(VideoStatus.READY)
                .urlMp4("http://example.com/video.mp4")
                .thumbnail("http://example.com/thumb.jpg")
                .user(testUser)
                .createdAt(OffsetDateTime.now())
                .build();
        
        // Set upload directory to temp directory for tests
        ReflectionTestUtils.setField(videoService, "uploadDir", System.getProperty("java.io.tmpdir"));
    }
    
    @Test
    void shouldGetVideoSuccessfully() {
        // Given
        when(videoRepository.findById(testVideoId)).thenReturn(Optional.of(testVideo));
        when(voteRepository.countByVideoIdAndDirection(testVideoId, VoteDirection.LIKE)).thenReturn(10L);
        when(voteRepository.countByVideoIdAndDirection(testVideoId, VoteDirection.NOT_LIKE)).thenReturn(2L);
        when(viewRepository.countByVideoId(testVideoId)).thenReturn(100L);
        
        // When
        VideoResponse response = videoService.getVideo(testVideoId);
        
        // Then
        assertThat(response).isNotNull();
        assertThat(response.getId()).isEqualTo(testVideoId.toString());
        assertThat(response.getTitle()).isEqualTo("Test Video");
        assertThat(response.getStats().getLikes()).isEqualTo(10L);
        assertThat(response.getStats().getNotLikes()).isEqualTo(2L);
        assertThat(response.getStats().getViews()).isEqualTo(100L);
        
        verify(videoRepository).findById(testVideoId);
    }
    
    @Test
    void shouldThrowExceptionWhenVideoNotFound() {
        // Given
        when(videoRepository.findById(testVideoId)).thenReturn(Optional.empty());
        
        // When/Then
        assertThatThrownBy(() -> videoService.getVideo(testVideoId))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("Video not found");
    }
    
    @Test
    void shouldUploadVideoSuccessfully() throws IOException {
        // Given
        MultipartFile file = new MockMultipartFile(
                "file", "test.mp4", "video/mp4", "test video content".getBytes());
        
        when(userRepository.findById(testUserId)).thenReturn(Optional.of(testUser));
        when(videoRepository.save(any(Video.class))).thenAnswer(invocation -> {
            Video video = invocation.getArgument(0);
            video.setId(testVideoId);
            return video;
        });
        when(videoRepository.findById(testVideoId)).thenReturn(Optional.of(testVideo));
        when(voteRepository.countByVideoIdAndDirection(any(), any())).thenReturn(0L);
        when(viewRepository.countByVideoId(any())).thenReturn(0L);
        
        // When
        VideoResponse response = videoService.uploadVideo(testUserId, file, "Test Video", "Description");
        
        // Then
        assertThat(response).isNotNull();
        verify(videoRepository, atLeastOnce()).save(any(Video.class));
    }
    
    @Test
    void shouldThrowExceptionForInvalidFileFormat() {
        // Given
        MultipartFile file = new MockMultipartFile(
                "file", "test.txt", "text/plain", "test content".getBytes());
        
        // When/Then
        assertThatThrownBy(() -> videoService.uploadVideo(testUserId, file, "Title", "Description"))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("Invalid file format");
    }
    
    @Test
    void shouldVoteOnVideoSuccessfully() {
        // Given
        VoteRequest request = new VoteRequest();
        request.setDirection("like");
        
        when(videoRepository.findById(testVideoId)).thenReturn(Optional.of(testVideo));
        when(voteRepository.findByUserIdAndVideoId(testUserId, testVideoId))
                .thenReturn(Optional.empty());
        when(voteRepository.save(any(Vote.class))).thenAnswer(invocation -> invocation.getArgument(0));
        when(userLikedVideoRepository.existsByUserIdAndVideoId(testUserId, testVideoId))
                .thenReturn(false);
        
        // When
        VoteResponse response = videoService.voteOnVideo(testVideoId, request, testUserId, null);
        
        // Then
        assertThat(response).isNotNull();
        assertThat(response.getDirection()).isEqualTo("like");
        assertThat(response.getVideoId()).isEqualTo(testVideoId.toString());
        
        verify(voteRepository).save(any(Vote.class));
        verify(userLikedVideoRepository).save(any());
    }
    
    @Test
    void shouldRecordViewSuccessfully() {
        // Given
        ViewRequest request = new ViewRequest();
        request.setWatchedSeconds(30);
        
        when(videoRepository.findById(testVideoId)).thenReturn(Optional.of(testVideo));
        when(viewRepository.save(any(View.class))).thenAnswer(invocation -> invocation.getArgument(0));
        
        // When
        ViewResponse response = videoService.recordView(testVideoId, request, testUserId);
        
        // Then
        assertThat(response).isNotNull();
        assertThat(response.getMessage()).isEqualTo("View recorded");
        
        verify(viewRepository).save(any(View.class));
    }
    
    @Test
    void shouldShareVideoSuccessfully() {
        // Given
        ShareRequest request = new ShareRequest();
        UUID sessionId = UUID.randomUUID();
        request.setSharerSessionId(sessionId.toString());
        
        ShareLink shareLink = ShareLink.builder()
                .id(UUID.randomUUID())
                .sharerSessionId(sessionId)
                .videoId(testVideoId)
                .build();
        
        when(videoRepository.findById(testVideoId)).thenReturn(Optional.of(testVideo));
        when(shareLinkRepository.save(any(ShareLink.class))).thenReturn(shareLink);
        
        // When
        ShareResponse response = videoService.shareVideo(testVideoId, request);
        
        // Then
        assertThat(response).isNotNull();
        assertThat(response.getVideoId()).isEqualTo(testVideoId.toString());
        
        verify(shareLinkRepository).save(any(ShareLink.class));
    }
    
    @Test
    void shouldDeleteVideoSuccessfully() {
        // Given
        when(videoRepository.findById(testVideoId)).thenReturn(Optional.of(testVideo));
        
        // When
        videoService.deleteVideo(testVideoId, testUserId);
        
        // Then
        verify(videoRepository).delete(testVideo);
    }
    
    @Test
    void shouldThrowExceptionWhenDeletingOtherUsersVideo() {
        // Given
        UUID otherUserId = UUID.randomUUID();
        when(videoRepository.findById(testVideoId)).thenReturn(Optional.of(testVideo));
        
        // When/Then
        assertThatThrownBy(() -> videoService.deleteVideo(testVideoId, otherUserId))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("Not authorized");
    }
}

