package com.short5.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "reports", indexes = {
    @Index(name = "idx_reports_reporter_id", columnList = "reporter_id"),
    @Index(name = "idx_reports_report_type", columnList = "report_type"),
    @Index(name = "idx_reports_target_id", columnList = "target_id"),
    @Index(name = "idx_reports_status", columnList = "status"),
    @Index(name = "idx_reports_created_at", columnList = "created_at")
})
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Report {
    
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", columnDefinition = "UUID")
    private UUID id;
    
    @Column(name = "reporter_id", columnDefinition = "UUID", nullable = false)
    private UUID reporterId;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "reporter_id", insertable = false, updatable = false)
    private User reporter;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "report_type", nullable = false, columnDefinition = "report_type")
    private ReportType reportType;
    
    @Column(name = "target_id", columnDefinition = "UUID", nullable = false)
    private UUID targetId;
    
    @Column(name = "reason", columnDefinition = "TEXT")
    private String reason;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, columnDefinition = "report_status")
    @Builder.Default
    private ReportStatus status = ReportStatus.PENDING;
    
    @Column(name = "resolved_by", columnDefinition = "UUID")
    private UUID resolvedBy;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "resolved_by", insertable = false, updatable = false)
    private User resolver;
    
    @Column(name = "resolved_at")
    private OffsetDateTime resolvedAt;
    
    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;
    
    @UpdateTimestamp
    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;
    
    public enum ReportType {
        VIDEO,
        USER
    }
    
    public enum ReportStatus {
        PENDING,
        RESOLVED,
        DISMISSED
    }
}

