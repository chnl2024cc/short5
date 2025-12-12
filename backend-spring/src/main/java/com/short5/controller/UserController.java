package com.short5.controller;

import com.short5.dto.UserProfileResponse;
import com.short5.dto.VideoResponse;
import com.short5.security.JwtService;
import com.short5.service.UserService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class UserController {
    
    private final UserService userService;
    private final JwtService jwtService;
    
    @GetMapping("/me")
    public ResponseEntity<UserProfileResponse> getCurrentUserProfile(Authentication authentication) {
        try {
            UUID userId = getUserIdFromAuthentication(authentication);
            UserProfileResponse response = userService.getCurrentUserProfile(userId);
            return ResponseEntity.ok(response);
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    @GetMapping("/me/videos")
    public ResponseEntity<List<VideoResponse>> getMyVideos(
            Authentication authentication,
            @RequestParam(required = false) String cursor,
            @RequestParam(defaultValue = "20") int limit) {
        try {
            UUID userId = getUserIdFromAuthentication(authentication);
            List<VideoResponse> videos = userService.getUserVideos(userId, cursor, limit);
            return ResponseEntity.ok(videos);
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    @GetMapping("/me/liked")
    public ResponseEntity<List<VideoResponse>> getLikedVideos(
            Authentication authentication,
            @RequestParam(required = false) String cursor,
            @RequestParam(defaultValue = "20") int limit) {
        try {
            UUID userId = getUserIdFromAuthentication(authentication);
            List<VideoResponse> videos = userService.getLikedVideos(userId, cursor, limit);
            return ResponseEntity.ok(videos);
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    @GetMapping("/{userId}")
    public ResponseEntity<Map<String, Object>> getUserProfile(@PathVariable String userId) {
        try {
            UUID id = UUID.fromString(userId);
            Map<String, Object> profile = userService.getPublicUserProfile(id);
            return ResponseEntity.ok(profile);
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

