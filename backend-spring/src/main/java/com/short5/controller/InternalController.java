package com.short5.controller;

import com.short5.service.VideoProcessingService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.UUID;

/**
 * Internal endpoints for system-to-system communication.
 * 
 * These endpoints are used by:
 * - Video worker (processing completion callbacks)
 * - Internal services
 * 
 * Note: These should be secured in production (e.g., API key, internal network only)
 */
@RestController
@RequestMapping("/api/v1/internal")
@RequiredArgsConstructor
@Slf4j
public class InternalController {
    
    private final VideoProcessingService videoProcessingService;
    
    /**
     * Callback endpoint for video processing completion.
     * Called by video_worker when processing is complete.
     * 
     * @param videoId The video ID
     * @param processingResult Processing result with status, URLs, and metadata
     * @return Success response
     */
    @PostMapping("/videos/{videoId}/processing-complete")
    public ResponseEntity<Map<String, String>> handleProcessingComplete(
            @PathVariable String videoId,
            @RequestBody Map<String, Object> processingResult) {
        try {
            UUID id = UUID.fromString(videoId);
            videoProcessingService.handleProcessingComplete(id, processingResult);
            
            return ResponseEntity.ok(Map.of("status", "success", "message", "Processing result received"));
        } catch (Exception e) {
            log.error("Error handling processing completion for video {}: {}", videoId, e.getMessage(), e);
            return ResponseEntity.badRequest()
                    .body(Map.of("status", "error", "message", e.getMessage()));
        }
    }
}

