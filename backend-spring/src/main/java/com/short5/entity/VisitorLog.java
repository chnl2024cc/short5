package com.short5.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "visitor_logs")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class VisitorLog {
    
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", columnDefinition = "UUID")
    private UUID id;
    
    @Column(name = "session_id", columnDefinition = "UUID", nullable = false)
    private UUID sessionId;
    
    @Column(name = "user_id", columnDefinition = "UUID")
    private UUID userId;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", insertable = false, updatable = false)
    private User user;
    
    @Column(name = "url", columnDefinition = "TEXT", nullable = false)
    private String url;
    
    @Column(name = "ip_address", columnDefinition = "INET")
    private String ipAddress;
    
    @Column(name = "user_agent", columnDefinition = "TEXT")
    private String userAgent;
    
    @Column(name = "country", length = 2)
    private String country;
    
    @Column(name = "country_name", length = 100)
    private String countryName;
    
    @Column(name = "city", length = 100)
    private String city;
    
    @Column(name = "latitude", precision = 10, scale = 8)
    private BigDecimal latitude;
    
    @Column(name = "longitude", precision = 11, scale = 8)
    private BigDecimal longitude;
    
    @CreationTimestamp
    @Column(name = "visited_at", nullable = false, updatable = false)
    private OffsetDateTime visitedAt;
}

