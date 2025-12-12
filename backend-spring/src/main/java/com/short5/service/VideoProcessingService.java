package com.short5.service;

import com.short5.entity.Video;
import com.short5.entity.Video.VideoStatus;
import com.short5.repository.VideoRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;

/**
 * Service for integrating with video processing worker (Celery via HTTP bridge).
 * 
 * This service sends video processing tasks to the video_worker via HTTP.
 * The video_worker (FastAPI) receives the task and dispatches it to Celery.
 * 
 * Alternative approaches:
 * 1. Direct Redis/Celery integration (requires Java Celery client)
 * 2. HTTP bridge (current implementation - simpler, uses existing FastAPI endpoint)
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class VideoProcessingService {
    
    private final VideoRepository videoRepository;
    private final RestTemplate restTemplate;
    
    @Value("${celery.task-gateway-url:http://localhost:8000/api/v1/internal/tasks}")
    private String taskGatewayUrl;
    
    @Value("${backend.base-url:http://localhost:8080}")
    private String backendBaseUrl;
    
    /**
     * Triggers video processing asynchronously.
     * Sends task to video_worker via HTTP bridge.
     * 
     * @param videoId The video ID to process
     * @return CompletableFuture that completes when task is submitted
     */
    @Async
    public CompletableFuture<Void> triggerVideoProcessing(UUID videoId) {
        try {
            Video video = videoRepository.findById(videoId)
                    .orElseThrow(() -> new RuntimeException("Video not found: " + videoId));
            
            // Build task payload
            Map<String, Object> taskPayload = new HashMap<>();
            taskPayload.put("video_id", videoId.toString());
            taskPayload.put("original_file_path", getOriginalFilePath(video));
            taskPayload.put("processed_dir", getProcessedDirPath(videoId));
            taskPayload.put("callback_url", backendBaseUrl + "/api/v1/internal/videos/" + videoId + "/processing-complete");
            
            log.info("Sending video processing task for video {} to gateway: {}", videoId, taskGatewayUrl);
            
            // Send task to video_worker gateway
            try {
                restTemplate.postForObject(taskGatewayUrl + "/process-video", taskPayload, Map.class);
                log.info("Video processing task submitted successfully for video {}", videoId);
            } catch (RestClientException e) {
                log.error("Failed to submit video processing task for video {}: {}", videoId, e.getMessage());
                // Update video status to failed
                video.setStatus(VideoStatus.FAILED);
                video.setErrorReason("Failed to submit processing task: " + e.getMessage());
                videoRepository.save(video);
            }
            
        } catch (Exception e) {
            log.error("Error triggering video processing for video {}: {}", videoId, e.getMessage(), e);
        }
        
        return CompletableFuture.completedFuture(null);
    }
    
    /**
     * Handles video processing completion callback from video_worker.
     * Updates video status and URLs based on processing results.
     * 
     * @param videoId The video ID
     * @param processingResult Processing result with URLs and metadata
     */
    public void handleProcessingComplete(UUID videoId, Map<String, Object> processingResult) {
        try {
            Video video = videoRepository.findById(videoId)
                    .orElseThrow(() -> new RuntimeException("Video not found: " + videoId));
            
            boolean success = Boolean.parseBoolean(processingResult.getOrDefault("success", "false").toString());
            
            if (success) {
                video.setStatus(VideoStatus.READY);
                video.setUrlMp4((String) processingResult.get("url_mp4"));
                video.setThumbnail((String) processingResult.get("thumbnail"));
                
                if (processingResult.containsKey("duration_seconds")) {
                    video.setDurationSeconds(Integer.parseInt(processingResult.get("duration_seconds").toString()));
                }
                
                log.info("Video {} processing completed successfully", videoId);
            } else {
                video.setStatus(VideoStatus.FAILED);
                video.setErrorReason((String) processingResult.getOrDefault("error", "Unknown processing error"));
                log.error("Video {} processing failed: {}", videoId, video.getErrorReason());
            }
            
            videoRepository.save(video);
            
        } catch (Exception e) {
            log.error("Error handling processing completion for video {}: {}", videoId, e.getMessage(), e);
        }
    }
    
    private String getOriginalFilePath(Video video) {
        // Extract file extension from original filename
        String ext = ".mp4";
        if (video.getOriginalFilename() != null && video.getOriginalFilename().contains(".")) {
            ext = video.getOriginalFilename().substring(video.getOriginalFilename().lastIndexOf('.'));
        }
        return String.format("/app/uploads/originals/%s%s", video.getId(), ext);
    }
    
    private String getProcessedDirPath(UUID videoId) {
        return String.format("/app/uploads/processed/%s", videoId);
    }
}

