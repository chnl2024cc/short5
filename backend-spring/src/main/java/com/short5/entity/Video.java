package com.short5.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.math.BigInteger;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "videos", indexes = {
    @Index(name = "idx_videos_user_id", columnList = "user_id"),
    @Index(name = "idx_videos_status", columnList = "status"),
    @Index(name = "idx_videos_created_at", columnList = "created_at")
})
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Video {
    
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", columnDefinition = "UUID")
    private UUID id;
    
    @Column(name = "user_id", columnDefinition = "UUID", nullable = false)
    private UUID userId;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", insertable = false, updatable = false)
    private User user;
    
    @Column(name = "title", length = 255)
    private String title;
    
    @Column(name = "description", columnDefinition = "TEXT")
    private String description;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, columnDefinition = "video_status")
    @Builder.Default
    private VideoStatus status = VideoStatus.UPLOADING;
    
    @Column(name = "url_mp4", columnDefinition = "TEXT")
    private String urlMp4;
    
    @Column(name = "thumbnail", columnDefinition = "TEXT")
    private String thumbnail;
    
    @Column(name = "duration_seconds")
    private Integer durationSeconds;
    
    @Column(name = "file_size_bytes")
    private BigInteger fileSizeBytes;
    
    @Column(name = "original_filename", length = 255)
    private String originalFilename;
    
    @Column(name = "error_reason", columnDefinition = "TEXT")
    private String errorReason;
    
    @Column(name = "video_metadata_json", columnDefinition = "TEXT")
    private String videoMetadataJson;
    
    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;
    
    @UpdateTimestamp
    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;
    
    public enum VideoStatus {
        UPLOADING,
        PROCESSING,
        READY,
        FAILED,
        REJECTED
    }
}

