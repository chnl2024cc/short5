package com.short5.service;

import com.short5.entity.ShareLink;
import com.short5.entity.ShareClick;
import com.short5.entity.Video;
import com.short5.repository.ShareLinkRepository;
import com.short5.repository.ShareClickRepository;
import com.short5.repository.VideoRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class ShareAnalyticsService {
    
    private final ShareLinkRepository shareLinkRepository;
    private final ShareClickRepository shareClickRepository;
    private final VideoRepository videoRepository;
    
    @Transactional(readOnly = true)
    public Map<String, Object> getShareAnalytics(String period, int days, UUID videoId) {
        OffsetDateTime endDate = OffsetDateTime.now();
        OffsetDateTime startDate = endDate.minusDays(days);
        
        // Filter shares and clicks by date and optionally video
        List<ShareLink> shares = shareLinkRepository.findAll().stream()
                .filter(s -> s.getCreatedAt().isAfter(startDate))
                .filter(s -> videoId == null || s.getVideoId().equals(videoId))
                .collect(Collectors.toList());
        
        List<ShareClick> clicks = shareClickRepository.findAll().stream()
                .filter(c -> c.getClickedAt().isAfter(startDate))
                .filter(c -> videoId == null || c.getVideoId().equals(videoId))
                .collect(Collectors.toList());
        
        long totalShares = shares.size();
        long totalClicks = clicks.size();
        
        // Unique clickers
        long uniqueClickers = clicks.stream()
                .map(ShareClick::getClickerSessionId)
                .distinct()
                .count();
        
        // Shares with clicks
        long sharesWithClicks = clicks.stream()
                .map(ShareClick::getShareLinkId)
                .distinct()
                .count();
        
        // Calculate metrics
        double clickThroughRate = totalShares > 0 ? (double) totalClicks / totalShares * 100 : 0;
        double avgClicksPerShare = totalShares > 0 ? (double) totalClicks / totalShares : 0;
        double shareConversionRate = totalShares > 0 ? (double) sharesWithClicks / totalShares * 100 : 0;
        double avgClicksPerClicker = uniqueClickers > 0 ? (double) totalClicks / uniqueClickers : 0;
        
        // Most shared videos
        Map<UUID, Long> videoShareCounts = shares.stream()
                .collect(Collectors.groupingBy(ShareLink::getVideoId, Collectors.counting()));
        
        List<Map<String, Object>> mostSharedVideos = videoShareCounts.entrySet().stream()
                .sorted(Map.Entry.<UUID, Long>comparingByValue().reversed())
                .limit(10)
                .map(entry -> {
                    Video video = videoRepository.findById(entry.getKey()).orElse(null);
                    Map<String, Object> videoData = new HashMap<>();
                    videoData.put("video_id", entry.getKey().toString());
                    videoData.put("title", video != null ? video.getTitle() : "Unknown");
                    videoData.put("share_count", entry.getValue());
                    return videoData;
                })
                .collect(Collectors.toList());
        
        // Most clicked videos
        Map<UUID, Long> videoClickCounts = clicks.stream()
                .collect(Collectors.groupingBy(ShareClick::getVideoId, Collectors.counting()));
        
        List<Map<String, Object>> mostClickedVideos = videoClickCounts.entrySet().stream()
                .sorted(Map.Entry.<UUID, Long>comparingByValue().reversed())
                .limit(10)
                .map(entry -> {
                    Video video = videoRepository.findById(entry.getKey()).orElse(null);
                    Map<String, Object> videoData = new HashMap<>();
                    videoData.put("video_id", entry.getKey().toString());
                    videoData.put("title", video != null ? video.getTitle() : "Unknown");
                    videoData.put("click_count", entry.getValue());
                    return videoData;
                })
                .collect(Collectors.toList());
        
        Map<String, Object> result = new HashMap<>();
        result.put("period", period);
        result.put("days", days);
        result.put("video_id", videoId != null ? videoId.toString() : null);
        result.put("summary", Map.of(
            "total_shares", totalShares,
            "total_clicks", totalClicks,
            "unique_clickers", uniqueClickers,
            "shares_with_clicks", sharesWithClicks
        ));
        result.put("metrics", Map.of(
            "click_through_rate", Math.round(clickThroughRate * 100.0) / 100.0,
            "avg_clicks_per_share", Math.round(avgClicksPerShare * 100.0) / 100.0,
            "share_conversion_rate", Math.round(shareConversionRate * 100.0) / 100.0,
            "avg_clicks_per_clicker", Math.round(avgClicksPerClicker * 100.0) / 100.0,
            "avg_time_to_first_click_hours", 0.0 // Would calculate from actual data
        ));
        result.put("over_time", Map.of(
            "shares", new ArrayList<>(), // Would group by period
            "clicks", new ArrayList<>()
        ));
        result.put("top_videos", Map.of(
            "most_shared", mostSharedVideos,
            "most_clicked", mostClickedVideos
        ));
        result.put("top_sharers", new ArrayList<>()); // Would calculate from session IDs
        
        return result;
    }
    
    @Transactional(readOnly = true)
    public Map<String, Object> getShareStats() {
        long totalShares = shareLinkRepository.count();
        long totalClicks = shareClickRepository.count();
        
        long uniqueClickers = shareClickRepository.findAll().stream()
                .map(ShareClick::getClickerSessionId)
                .distinct()
                .count();
        
        long sharesWithClicks = shareClickRepository.findAll().stream()
                .map(ShareClick::getShareLinkId)
                .distinct()
                .count();
        
        double clickThroughRate = totalShares > 0 ? (double) totalClicks / totalShares * 100 : 0;
        double avgClicksPerShare = totalShares > 0 ? (double) totalClicks / totalShares : 0;
        double shareConversionRate = totalShares > 0 ? (double) sharesWithClicks / totalShares * 100 : 0;
        
        Map<String, Object> stats = new HashMap<>();
        stats.put("total_shares", totalShares);
        stats.put("total_clicks", totalClicks);
        stats.put("unique_clickers", uniqueClickers);
        stats.put("shares_with_clicks", sharesWithClicks);
        stats.put("click_through_rate", Math.round(clickThroughRate * 100.0) / 100.0);
        stats.put("avg_clicks_per_share", Math.round(avgClicksPerShare * 100.0) / 100.0);
        stats.put("share_conversion_rate", Math.round(shareConversionRate * 100.0) / 100.0);
        
        return stats;
    }
}

