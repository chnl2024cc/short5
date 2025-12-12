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
@Table(name = "share_clicks", indexes = {
    @Index(name = "idx_share_clicks_share_link_id", columnList = "share_link_id"),
    @Index(name = "idx_share_clicks_clicker_session_id", columnList = "clicker_session_id"),
    @Index(name = "idx_share_clicks_video_id", columnList = "video_id"),
    @Index(name = "idx_share_clicks_clicked_at", columnList = "clicked_at")
})
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ShareClick {
    
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", columnDefinition = "UUID")
    private UUID id;
    
    @Column(name = "share_link_id", columnDefinition = "UUID", nullable = false)
    private UUID shareLinkId;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "share_link_id", insertable = false, updatable = false)
    private ShareLink shareLink;
    
    @Column(name = "clicker_session_id", columnDefinition = "UUID", nullable = false)
    private UUID clickerSessionId;
    
    @Column(name = "video_id", columnDefinition = "UUID", nullable = false)
    private UUID videoId;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "video_id", insertable = false, updatable = false)
    private Video video;
    
    @CreationTimestamp
    @Column(name = "clicked_at", nullable = false, updatable = false)
    private OffsetDateTime clickedAt;
}

