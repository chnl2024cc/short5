package com.short5.service;

import com.short5.entity.Video;
import com.short5.entity.Video.VideoStatus;
import com.short5.repository.VideoRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.time.OffsetDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class VideoProcessingServiceTest {
    
    @Mock
    private VideoRepository videoRepository;
    
    @Mock
    private RestTemplate restTemplate;
    
    @InjectMocks
    private VideoProcessingService videoProcessingService;
    
    private Video testVideo;
    private UUID testVideoId;
    
    @BeforeEach
    void setUp() {
        testVideoId = UUID.randomUUID();
        testVideo = Video.builder()
                .id(testVideoId)
                .userId(UUID.randomUUID())
                .title("Test Video")
                .status(VideoStatus.PROCESSING)
                .originalFilename("test.mp4")
                .createdAt(OffsetDateTime.now())
                .build();
        
        // Set configuration values
        ReflectionTestUtils.setField(videoProcessingService, "taskGatewayUrl", 
                "http://localhost:8000/api/v1/internal/tasks");
        ReflectionTestUtils.setField(videoProcessingService, "backendBaseUrl", 
                "http://localhost:8080");
    }
    
    @Test
    void shouldTriggerVideoProcessingSuccessfully() throws InterruptedException {
        // Given
        when(videoRepository.findById(testVideoId)).thenReturn(Optional.of(testVideo));
        when(restTemplate.postForObject(anyString(), any(), eq(Map.class)))
                .thenReturn(new HashMap<>());
        
        // When
        CompletableFuture<Void> future = videoProcessingService.triggerVideoProcessing(testVideoId);
        
        // Then
        assertThat(future).isNotNull();
        // Wait for async completion (with timeout)
        future.join();
        
        // Give async method time to execute
        Thread.sleep(100);
        
        verify(videoRepository).findById(testVideoId);
        verify(restTemplate).postForObject(
                eq("http://localhost:8000/api/v1/internal/tasks/process-video"),
                any(Map.class),
                eq(Map.class));
    }
    
    @Test
    void shouldHandleProcessingTaskSubmissionFailure() throws InterruptedException {
        // Given
        when(videoRepository.findById(testVideoId)).thenReturn(Optional.of(testVideo));
        when(restTemplate.postForObject(anyString(), any(), eq(Map.class)))
                .thenThrow(new RestClientException("Connection failed"));
        when(videoRepository.save(any(Video.class))).thenAnswer(invocation -> invocation.getArgument(0));
        
        // When
        CompletableFuture<Void> future = videoProcessingService.triggerVideoProcessing(testVideoId);
        
        // Then
        future.join(); // Wait for completion
        Thread.sleep(100); // Give async method time to execute
        
        verify(videoRepository, atLeastOnce()).findById(testVideoId);
        verify(videoRepository, atLeastOnce()).save(any(Video.class));
        
        // Verify video status was updated to FAILED
        verify(videoRepository).save(argThat(video -> 
                video.getStatus() == VideoStatus.FAILED && 
                video.getErrorReason() != null));
    }
    
    @Test
    void shouldHandleVideoNotFound() throws InterruptedException {
        // Given
        when(videoRepository.findById(testVideoId)).thenReturn(Optional.empty());
        
        // When
        CompletableFuture<Void> future = videoProcessingService.triggerVideoProcessing(testVideoId);
        
        // Then
        future.join(); // Should complete without error
        Thread.sleep(100); // Give async method time to execute
        
        verify(videoRepository).findById(testVideoId);
        verify(restTemplate, never()).postForObject(anyString(), any(), any());
    }
    
    @Test
    void shouldHandleProcessingCompleteSuccessfully() {
        // Given
        Map<String, Object> processingResult = new HashMap<>();
        processingResult.put("success", true);
        processingResult.put("url_mp4", "http://example.com/video.mp4");
        processingResult.put("thumbnail", "http://example.com/thumb.jpg");
        processingResult.put("duration_seconds", 120);
        
        when(videoRepository.findById(testVideoId)).thenReturn(Optional.of(testVideo));
        when(videoRepository.save(any(Video.class))).thenAnswer(invocation -> invocation.getArgument(0));
        
        // When
        videoProcessingService.handleProcessingComplete(testVideoId, processingResult);
        
        // Then
        verify(videoRepository).save(argThat(video -> 
                video.getStatus() == VideoStatus.READY &&
                video.getUrlMp4().equals("http://example.com/video.mp4") &&
                video.getThumbnail().equals("http://example.com/thumb.jpg") &&
                video.getDurationSeconds() == 120));
    }
    
    @Test
    void shouldHandleProcessingCompleteFailure() {
        // Given
        Map<String, Object> processingResult = new HashMap<>();
        processingResult.put("success", false);
        processingResult.put("error", "Processing failed: codec error");
        
        when(videoRepository.findById(testVideoId)).thenReturn(Optional.of(testVideo));
        when(videoRepository.save(any(Video.class))).thenAnswer(invocation -> invocation.getArgument(0));
        
        // When
        videoProcessingService.handleProcessingComplete(testVideoId, processingResult);
        
        // Then
        verify(videoRepository).save(argThat(video -> 
                video.getStatus() == VideoStatus.FAILED &&
                video.getErrorReason().equals("Processing failed: codec error")));
    }
    
    @Test
    void shouldHandleProcessingCompleteWithVideoNotFound() {
        // Given
        Map<String, Object> processingResult = new HashMap<>();
        processingResult.put("success", true);
        
        when(videoRepository.findById(testVideoId)).thenReturn(Optional.empty());
        
        // When
        videoProcessingService.handleProcessingComplete(testVideoId, processingResult);
        
        // Then
        verify(videoRepository).findById(testVideoId);
        verify(videoRepository, never()).save(any(Video.class));
    }
}

