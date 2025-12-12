package com.short5.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.OffsetDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserProfileResponse {
    private String id;
    private String username;
    private String email;
    private Boolean isAdmin;
    private OffsetDateTime createdAt;
    private UserStats stats;
    
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class UserStats {
        private Long videosUploaded = 0L;
        private Long totalLikesReceived = 0L;
        private Long totalViews = 0L;
    }
}

