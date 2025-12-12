package com.short5.controller;

import com.short5.dto.*;
import com.short5.security.JwtService;
import com.short5.service.VideoService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/videos")
@RequiredArgsConstructor
public class VideoController {
    
    private final VideoService videoService;
    
    @GetMapping("/{videoId}")
    public ResponseEntity<VideoResponse> getVideo(@PathVariable String videoId) {
        try {
            UUID id = UUID.fromString(videoId);
            VideoResponse response = videoService.getVideo(id);
            return ResponseEntity.ok(response);
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    @PostMapping("/upload")
    public ResponseEntity<VideoResponse> uploadVideo(
            Authentication authentication,
            @RequestParam("file") MultipartFile file,
            @RequestParam(required = false) String title,
            @RequestParam(required = false) String description) {
        try {
            UUID userId = getUserIdFromAuthentication(authentication);
            VideoResponse response = videoService.uploadVideo(userId, file, title, description);
            return ResponseEntity.status(HttpStatus.ACCEPTED).body(response);
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().build();
        } catch (IOException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
    
    @DeleteMapping("/{videoId}")
    public ResponseEntity<Void> deleteVideo(
            Authentication authentication,
            @PathVariable String videoId) {
        try {
            UUID id = UUID.fromString(videoId);
            UUID userId = getUserIdFromAuthentication(authentication);
            videoService.deleteVideo(id, userId);
            return ResponseEntity.noContent().build();
        } catch (RuntimeException e) {
            if (e.getMessage().contains("Not authorized")) {
                return ResponseEntity.status(HttpStatus.FORBIDDEN).build();
            }
            return ResponseEntity.notFound().build();
        }
    }
    
    @PostMapping("/{videoId}/vote")
    public ResponseEntity<VoteResponse> voteOnVideo(
            @PathVariable String videoId,
            @Valid @RequestBody VoteRequest request,
            Authentication authentication) {
        try {
            UUID id = UUID.fromString(videoId);
            UUID userId = authentication != null ? getUserIdFromAuthentication(authentication) : null;
            UUID sessionId = request.getSessionId() != null ? UUID.fromString(request.getSessionId()) : null;
            
            VoteResponse response = videoService.voteOnVideo(id, request, userId, sessionId);
            return ResponseEntity.ok(response);
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().build();
        }
    }
    
    @PostMapping("/{videoId}/view")
    public ResponseEntity<ViewResponse> recordView(
            @PathVariable String videoId,
            @Valid @RequestBody ViewRequest request,
            Authentication authentication) {
        try {
            UUID id = UUID.fromString(videoId);
            UUID userId = authentication != null ? getUserIdFromAuthentication(authentication) : null;
            ViewResponse response = videoService.recordView(id, request, userId);
            return ResponseEntity.ok(response);
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().build();
        }
    }
    
    @PostMapping("/{videoId}/share")
    public ResponseEntity<ShareResponse> shareVideo(
            @PathVariable String videoId,
            @Valid @RequestBody ShareRequest request) {
        try {
            UUID id = UUID.fromString(videoId);
            ShareResponse response = videoService.shareVideo(id, request);
            return ResponseEntity.ok(response);
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().build();
        }
    }
    
    @PostMapping("/{videoId}/share/click")
    public ResponseEntity<ShareClickResponse> trackShareClick(
            @PathVariable String videoId,
            @Valid @RequestBody ShareClickRequest request) {
        try {
            UUID id = UUID.fromString(videoId);
            ShareClickResponse response = videoService.trackShareClick(id, request);
            return ResponseEntity.ok(response);
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().build();
        }
    }
    
    @PostMapping("/{videoId}/like")
    public ResponseEntity<Void> likeVideo(
            Authentication authentication,
            @PathVariable String videoId) {
        try {
            UUID id = UUID.fromString(videoId);
            UUID userId = getUserIdFromAuthentication(authentication);
            videoService.likeVideo(id, userId);
            return ResponseEntity.ok().build();
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    @DeleteMapping("/{videoId}/like")
    public ResponseEntity<Void> unlikeVideo(
            Authentication authentication,
            @PathVariable String videoId) {
        try {
            UUID id = UUID.fromString(videoId);
            UUID userId = getUserIdFromAuthentication(authentication);
            videoService.unlikeVideo(id, userId);
            return ResponseEntity.noContent().build();
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    private UUID getUserIdFromAuthentication(Authentication authentication) {
        if (authentication == null || authentication.getPrincipal() == null) {
            throw new RuntimeException("Not authenticated");
        }
        
        UserDetails userDetails = (UserDetails) authentication.getPrincipal();
        return UUID.fromString(userDetails.getUsername());
    }
}

