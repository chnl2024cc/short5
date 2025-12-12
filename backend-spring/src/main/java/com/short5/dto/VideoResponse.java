package com.short5.dto;

import com.short5.entity.Video;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.OffsetDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class VideoResponse {
    private String id;
    private String title;
    private String description;
    private String status;
    private String thumbnail;
    private String urlMp4;
    private Integer durationSeconds;
    private String errorReason;
    private UserBasic user;
    private VideoStats stats;
    private OffsetDateTime createdAt;
    
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class UserBasic {
        private String id;
        private String username;
    }
    
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class VideoStats {
        private Long likes = 0L;
        private Long notLikes = 0L;
        private Long views = 0L;
    }
}

