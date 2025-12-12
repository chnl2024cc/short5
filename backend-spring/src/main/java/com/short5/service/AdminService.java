package com.short5.service;

import com.short5.dto.*;
import com.short5.entity.*;
import com.short5.entity.Report.ReportStatus;
import com.short5.entity.Report.ReportType;
import com.short5.entity.Video.VideoStatus;
import com.short5.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.OffsetDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class AdminService {
    
    private final VideoRepository videoRepository;
    private final ReportRepository reportRepository;
    private final UserRepository userRepository;
    private final VoteRepository voteRepository;
    private final ViewRepository viewRepository;
    
    @Value("${file.upload-dir:/app/uploads}")
    private String uploadDir;
    
    @Transactional(readOnly = true)
    public List<VideoResponse> getAllVideos(String status, String cursor, int limit) {
        Pageable pageable = PageRequest.of(0, Math.min(limit, 100));
        Page<Video> videoPage;
        
        if (status != null && !status.isEmpty()) {
            try {
                VideoStatus videoStatus = VideoStatus.valueOf(status.toUpperCase());
                videoPage = videoRepository.findByStatusOrderByCreatedAtDesc(videoStatus, pageable);
            } catch (IllegalArgumentException e) {
                videoPage = videoRepository.findAll(pageable);
            }
        } else {
            videoPage = videoRepository.findAll(pageable);
        }
        
        return videoPage.getContent().stream()
                .map(this::convertToVideoResponse)
                .collect(Collectors.toList());
    }
    
    @Transactional(readOnly = true)
    public List<VideoResponse> getPendingVideos(String cursor, int limit) {
        List<Video> videos = videoRepository.findAll().stream()
                .filter(v -> v.getStatus() == VideoStatus.PROCESSING || v.getStatus() == VideoStatus.UPLOADING)
                .sorted((a, b) -> b.getCreatedAt().compareTo(a.getCreatedAt()))
                .limit(Math.min(limit, 100))
                .collect(Collectors.toList());
        
        return videos.stream()
                .map(this::convertToVideoResponse)
                .collect(Collectors.toList());
    }
    
    @Transactional
    public void approveVideo(UUID videoId) {
        Video video = videoRepository.findById(videoId)
                .orElseThrow(() -> new RuntimeException("Video not found"));
        
        video.setStatus(VideoStatus.READY);
        videoRepository.save(video);
    }
    
    @Transactional
    public void rejectVideo(UUID videoId, RejectVideoRequest request) {
        Video video = videoRepository.findById(videoId)
                .orElseThrow(() -> new RuntimeException("Video not found"));
        
        video.setStatus(VideoStatus.REJECTED);
        video.setErrorReason(request.getReason());
        videoRepository.save(video);
    }
    
    @Transactional
    public void deleteVideoAdmin(UUID videoId) {
        Video video = videoRepository.findById(videoId)
                .orElseThrow(() -> new RuntimeException("Video not found"));
        
        // Delete files
        try {
            Path uploadPath = Paths.get(uploadDir);
            String originalExt = video.getOriginalFilename() != null 
                    ? video.getOriginalFilename().substring(video.getOriginalFilename().lastIndexOf('.'))
                    : ".mp4";
            Path originalFile = uploadPath.resolve("originals").resolve(video.getId() + originalExt);
            Files.deleteIfExists(originalFile);
            
            Path processedDir = uploadPath.resolve("processed").resolve(video.getId().toString());
            if (Files.exists(processedDir)) {
                Files.walk(processedDir)
                        .sorted((a, b) -> -a.compareTo(b))
                        .forEach(path -> {
                            try {
                                Files.delete(path);
                            } catch (IOException e) {
                                log.warn("Failed to delete file: {}", path, e);
                            }
                        });
            }
        } catch (IOException e) {
            log.error("Error deleting video files: {}", e.getMessage());
        }
        
        videoRepository.delete(video);
    }
    
    @Transactional(readOnly = true)
    public Map<String, Object> getReports(ReportStatus status, String cursor, int limit) {
        List<Report> reports = status != null 
                ? reportRepository.findByStatusOrderByCreatedAtDesc(status)
                : reportRepository.findAll();
        
        if (cursor != null) {
            try {
                OffsetDateTime cursorTime = OffsetDateTime.parse(cursor);
                reports = reports.stream()
                        .filter(r -> r.getCreatedAt().isBefore(cursorTime))
                        .collect(Collectors.toList());
            } catch (Exception e) {
                log.warn("Invalid cursor format: {}", cursor);
            }
        }
        
        reports = reports.stream()
                .limit(Math.min(limit, 100))
                .collect(Collectors.toList());
        
        List<Map<String, Object>> reportsData = reports.stream()
                .map(this::convertReportToMap)
                .collect(Collectors.toList());
        
        Map<String, Object> result = new HashMap<>();
        result.put("reports", reportsData);
        result.put("next_cursor", reports.isEmpty() ? null : reports.get(reports.size() - 1).getCreatedAt().toString());
        result.put("has_more", reports.size() == limit);
        
        return result;
    }
    
    @Transactional
    public Map<String, Object> resolveReport(UUID reportId, UUID resolverId, ResolveReportRequest request) {
        Report report = reportRepository.findById(reportId)
                .orElseThrow(() -> new RuntimeException("Report not found"));
        
        if (report.getStatus() != ReportStatus.PENDING) {
            throw new RuntimeException("Report is already " + report.getStatus().name());
        }
        
        if ("resolve".equalsIgnoreCase(request.getAction())) {
            report.setStatus(ReportStatus.RESOLVED);
        } else if ("dismiss".equalsIgnoreCase(request.getAction())) {
            report.setStatus(ReportStatus.DISMISSED);
        } else {
            throw new RuntimeException("Invalid action. Must be 'resolve' or 'dismiss'");
        }
        
        report.setResolvedBy(resolverId);
        report.setResolvedAt(OffsetDateTime.now());
        reportRepository.save(report);
        
        Map<String, Object> result = new HashMap<>();
        result.put("message", "Report " + request.getAction().toLowerCase() + "ed");
        result.put("report_id", report.getId().toString());
        result.put("status", report.getStatus().name());
        
        return result;
    }
    
    @Transactional(readOnly = true)
    public Map<String, Object> getUsers(String cursor, int limit, String search) {
        List<User> users = userRepository.findAll();
        
        if (search != null && !search.isEmpty()) {
            String searchLower = search.toLowerCase();
            users = users.stream()
                    .filter(u -> u.getUsername().toLowerCase().contains(searchLower) ||
                                u.getEmail().toLowerCase().contains(searchLower))
                    .collect(Collectors.toList());
        }
        
        users = users.stream()
                .sorted((a, b) -> b.getCreatedAt().compareTo(a.getCreatedAt()))
                .collect(Collectors.toList());
        
        if (cursor != null) {
            try {
                OffsetDateTime cursorTime = OffsetDateTime.parse(cursor);
                users = users.stream()
                        .filter(u -> u.getCreatedAt().isBefore(cursorTime))
                        .collect(Collectors.toList());
            } catch (Exception e) {
                log.warn("Invalid cursor format: {}", cursor);
            }
        }
        
        users = users.stream()
                .limit(Math.min(limit, 100))
                .collect(Collectors.toList());
        
        List<Map<String, Object>> usersData = users.stream()
                .map(user -> {
                    long videoCount = videoRepository.countByUserId(user.getId());
                    Map<String, Object> userData = new HashMap<>();
                    userData.put("id", user.getId().toString());
                    userData.put("username", user.getUsername());
                    userData.put("email", user.getEmail());
                    userData.put("is_admin", user.getIsAdmin());
                    userData.put("is_active", user.getIsActive());
                    userData.put("created_at", user.getCreatedAt().toString());
                    userData.put("video_count", videoCount);
                    return userData;
                })
                .collect(Collectors.toList());
        
        Map<String, Object> result = new HashMap<>();
        result.put("users", usersData);
        result.put("next_cursor", users.isEmpty() ? null : users.get(users.size() - 1).getCreatedAt().toString());
        result.put("has_more", users.size() == limit);
        
        return result;
    }
    
    @Transactional(readOnly = true)
    public Map<String, Object> getUserDetails(UUID userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));
        
        long videoCount = videoRepository.countByUserId(userId);
        Map<String, Long> videosByStatus = new HashMap<>();
        for (VideoStatus status : VideoStatus.values()) {
            videosByStatus.put(status.name().toLowerCase(), 
                videoRepository.findByUserIdOrderByCreatedAtDesc(userId).stream()
                    .filter(v -> v.getStatus() == status)
                    .count());
        }
        
        long reportsMade = reportRepository.findByReporterId(userId).size();
        long reportsAgainst = reportRepository.findByTargetId(userId).stream()
                .filter(r -> r.getReportType() == ReportType.USER)
                .count();
        
        Map<String, Object> userData = new HashMap<>();
        userData.put("id", user.getId().toString());
        userData.put("username", user.getUsername());
        userData.put("email", user.getEmail());
        userData.put("is_admin", user.getIsAdmin());
        userData.put("is_active", user.getIsActive());
        userData.put("created_at", user.getCreatedAt().toString());
        userData.put("updated_at", user.getUpdatedAt() != null ? user.getUpdatedAt().toString() : null);
        userData.put("stats", Map.of(
            "videos", Map.of(
                "total", videoCount,
                "by_status", videosByStatus
            ),
            "reports_made", reportsMade,
            "reports_against", reportsAgainst
        ));
        
        return userData;
    }
    
    @Transactional
    public Map<String, Object> updateUser(UUID userId, Map<String, Object> request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));
        
        if (request.containsKey("is_active")) {
            user.setIsActive((Boolean) request.get("is_active"));
        }
        if (request.containsKey("is_admin")) {
            user.setIsAdmin((Boolean) request.get("is_admin"));
        }
        
        user = userRepository.save(user);
        
        Map<String, Object> result = new HashMap<>();
        result.put("message", "User updated successfully");
        result.put("user_id", user.getId().toString());
        result.put("is_active", user.getIsActive());
        result.put("is_admin", user.getIsAdmin());
        
        return result;
    }
    
    private Map<String, Object> convertReportToMap(Report report) {
        Map<String, Object> reportData = new HashMap<>();
        reportData.put("id", report.getId().toString());
        reportData.put("type", report.getReportType().name().toLowerCase());
        reportData.put("target_id", report.getTargetId().toString());
        reportData.put("reason", report.getReason());
        reportData.put("status", report.getStatus().name().toLowerCase());
        reportData.put("created_at", report.getCreatedAt().toString());
        reportData.put("resolved_at", report.getResolvedAt() != null ? report.getResolvedAt().toString() : null);
        
        User reporter = report.getReporter();
        if (reporter == null) {
            reporter = userRepository.findById(report.getReporterId()).orElse(null);
        }
        if (reporter != null) {
            reportData.put("reporter", Map.of(
                "id", reporter.getId().toString(),
                "username", reporter.getUsername()
            ));
        }
        
        if (report.getResolvedBy() != null) {
            User resolver = userRepository.findById(report.getResolvedBy()).orElse(null);
            if (resolver != null) {
                reportData.put("resolver", Map.of(
                    "id", resolver.getId().toString(),
                    "username", resolver.getUsername()
                ));
            }
        }
        
        if (report.getReportType() == ReportType.VIDEO) {
            Video video = videoRepository.findById(report.getTargetId()).orElse(null);
            if (video != null) {
                User videoUser = userRepository.findById(video.getUserId()).orElse(null);
                Map<String, Object> targetInfo = new HashMap<>();
                targetInfo.put("id", video.getId().toString());
                targetInfo.put("title", video.getTitle());
                if (videoUser != null) {
                    targetInfo.put("user", Map.of(
                        "id", videoUser.getId().toString(),
                        "username", videoUser.getUsername()
                    ));
                }
                reportData.put("target", targetInfo);
            }
        } else {
            User targetUser = userRepository.findById(report.getTargetId()).orElse(null);
            if (targetUser != null) {
                reportData.put("target", Map.of(
                    "id", targetUser.getId().toString(),
                    "username", targetUser.getUsername()
                ));
            }
        }
        
        return reportData;
    }
    
    private VideoResponse convertToVideoResponse(Video video) {
        User user = video.getUser();
        if (user == null) {
            user = userRepository.findById(video.getUserId()).orElse(null);
        }
        
        long likes = voteRepository.countByVideoIdAndDirection(video.getId(), com.short5.entity.Vote.VoteDirection.LIKE);
        long views = viewRepository.countByVideoId(video.getId());
        
        VideoResponse.VideoStats stats = VideoResponse.VideoStats.builder()
                .likes(likes)
                .notLikes(0L)
                .views(views)
                .build();
        
        VideoResponse.UserBasic userBasic = null;
        if (user != null) {
            userBasic = VideoResponse.UserBasic.builder()
                    .id(user.getId().toString())
                    .username(user.getUsername())
                    .build();
        }
        
        return VideoResponse.builder()
                .id(video.getId().toString())
                .title(video.getTitle())
                .description(video.getDescription())
                .status(video.getStatus().name())
                .thumbnail(video.getThumbnail())
                .urlMp4(video.getUrlMp4())
                .durationSeconds(video.getDurationSeconds())
                .errorReason(video.getErrorReason())
                .user(userBasic)
                .stats(stats)
                .createdAt(video.getCreatedAt())
                .build();
    }
}
