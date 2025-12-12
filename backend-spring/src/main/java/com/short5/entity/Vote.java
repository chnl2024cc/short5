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
@Table(name = "votes", indexes = {
    @Index(name = "idx_votes_user_id", columnList = "user_id"),
    @Index(name = "idx_votes_session_id", columnList = "session_id"),
    @Index(name = "idx_votes_video_id", columnList = "video_id"),
    @Index(name = "idx_votes_direction", columnList = "direction")
})
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Vote {
    
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", columnDefinition = "UUID")
    private UUID id;
    
    @Column(name = "user_id", columnDefinition = "UUID")
    private UUID userId;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", insertable = false, updatable = false)
    private User user;
    
    @Column(name = "session_id", columnDefinition = "UUID")
    private UUID sessionId;
    
    @Column(name = "video_id", columnDefinition = "UUID", nullable = false)
    private UUID videoId;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "video_id", insertable = false, updatable = false)
    private Video video;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "direction", nullable = false, columnDefinition = "vote_direction")
    private VoteDirection direction;
    
    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;
    
    public enum VoteDirection {
        LIKE,
        NOT_LIKE
    }
}

