package com.short5.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "share_links", indexes = {
    @Index(name = "idx_share_links_sharer_session_id", columnList = "sharer_session_id"),
    @Index(name = "idx_share_links_video_id", columnList = "video_id"),
    @Index(name = "idx_share_links_created_at", columnList = "created_at")
})
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ShareLink {
    
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", columnDefinition = "UUID")
    private UUID id;
    
    @Column(name = "sharer_session_id", columnDefinition = "UUID", nullable = false)
    private UUID sharerSessionId;
    
    @Column(name = "video_id", columnDefinition = "UUID", nullable = false)
    private UUID videoId;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "video_id", insertable = false, updatable = false)
    private Video video;
    
    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;
}

