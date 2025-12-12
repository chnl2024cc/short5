package com.short5.service;

import com.short5.entity.*;
import com.short5.entity.Video.VideoStatus;
import com.short5.entity.Vote.VoteDirection;
import com.short5.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class AnalyticsService {
    
    private final VideoRepository videoRepository;
    private final UserRepository userRepository;
    private final VoteRepository voteRepository;
    private final ViewRepository viewRepository;
    private final ReportRepository reportRepository;
    private final ShareLinkRepository shareLinkRepository;
    private final ShareClickRepository shareClickRepository;
    private final VisitorLogRepository visitorLogRepository;
    
    @Transactional(readOnly = true)
    public Map<String, Object> getAdminStats() {
        Map<String, Object> stats = new HashMap<>();
        
        // Total users
        long totalUsers = userRepository.count();
        stats.put("users", Map.of("total", totalUsers));
        
        // Total videos and by status
        long totalVideos = videoRepository.count();
        Map<String, Long> videosByStatus = new HashMap<>();
        for (VideoStatus status : VideoStatus.values()) {
            videosByStatus.put(status.name().toLowerCase(), 
                (long) videoRepository.findByStatus(status).size());
        }
        stats.put("videos", Map.of(
            "total", totalVideos,
            "by_status", videosByStatus
        ));
        
        // Reports
        long totalReports = reportRepository.count();
        long pendingReports = reportRepository.findByStatusOrderByCreatedAtDesc(Report.ReportStatus.PENDING).size();
        stats.put("reports", Map.of(
            "total", totalReports,
            "pending", pendingReports
        ));
        
        return stats;
    }
    
    @Transactional(readOnly = true)
    public Map<String, Object> getAnalytics(String period, int days) {
        OffsetDateTime endDate = OffsetDateTime.now();
        OffsetDateTime startDate = endDate.minusDays(days);
        
        Map<String, Object> analytics = new HashMap<>();
        
        // Get views, likes, videos over time
        // Simplified - in production would use date_trunc SQL functions
        List<View> views = viewRepository.findAll().stream()
                .filter(v -> v.getCreatedAt().isAfter(startDate))
                .collect(Collectors.toList());
        
        List<Vote> likes = voteRepository.findAll().stream()
                .filter(v -> v.getDirection() == VoteDirection.LIKE && v.getCreatedAt().isAfter(startDate))
                .collect(Collectors.toList());
        
        List<Video> videos = videoRepository.findAll().stream()
                .filter(v -> v.getCreatedAt().isAfter(startDate))
                .collect(Collectors.toList());
        
        // Group by period (simplified - would use SQL date_trunc in production)
        Map<String, Long> viewsOverTime = groupByPeriod(views, View::getCreatedAt, period);
        Map<String, Long> likesOverTime = groupByPeriod(likes, Vote::getCreatedAt, period);
        Map<String, Long> videosOverTime = groupByPeriod(videos, Video::getCreatedAt, period);
        
        analytics.put("period", period);
        analytics.put("days", days);
        analytics.put("views", viewsOverTime);
        analytics.put("likes", likesOverTime);
        analytics.put("videos", videosOverTime);
        
        return analytics;
    }
    
    private <T> Map<String, Long> groupByPeriod(List<T> items, java.util.function.Function<T, OffsetDateTime> dateExtractor, String period) {
        Map<String, Long> grouped = new HashMap<>();
        for (T item : items) {
            OffsetDateTime date = dateExtractor.apply(item);
            String key = formatPeriod(date, period);
            grouped.put(key, grouped.getOrDefault(key, 0L) + 1);
        }
        return grouped;
    }
    
    private String formatPeriod(OffsetDateTime date, String period) {
        if ("day".equals(period)) {
            return date.toLocalDate().toString();
        } else {
            // Week - simplified
            return date.toLocalDate().toString();
        }
    }
}

