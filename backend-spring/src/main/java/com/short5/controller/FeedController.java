package com.short5.controller;

import com.short5.dto.FeedResponse;
import com.short5.security.JwtService;
import com.short5.service.FeedService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/feed")
@RequiredArgsConstructor
public class FeedController {
    
    private final FeedService feedService;
    
    @GetMapping
    public ResponseEntity<FeedResponse> getFeed(
            Authentication authentication,
            @RequestParam(required = false) String cursor,
            @RequestParam(defaultValue = "10") int limit) {
        try {
            UUID userId = null;
            if (authentication != null && authentication.getPrincipal() != null) {
                UserDetails userDetails = (UserDetails) authentication.getPrincipal();
                userId = UUID.fromString(userDetails.getUsername());
            }
            
            FeedResponse response = feedService.getFeed(userId, cursor, limit);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.ok(FeedResponse.builder()
                    .videos(java.util.List.of())
                    .nextCursor(null)
                    .hasMore(false)
                    .build());
        }
    }
}

