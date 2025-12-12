package com.short5.controller;

import com.short5.dto.*;
import com.short5.entity.Report;
import com.short5.entity.Report.ReportStatus;
import com.short5.entity.User;
import com.short5.security.JwtService;
import com.short5.service.AdminService;
import com.short5.service.AnalyticsService;
import com.short5.service.ShareAnalyticsService;
import com.short5.service.VisitorAnalyticsService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/admin")
@RequiredArgsConstructor
@PreAuthorize("hasAuthority('ROLE_ADMIN')")
public class AdminController {
    
    private final AdminService adminService;
    private final AnalyticsService analyticsService;
    private final ShareAnalyticsService shareAnalyticsService;
    private final VisitorAnalyticsService visitorAnalyticsService;
    
    @GetMapping("/videos")
    public ResponseEntity<List<VideoResponse>> getAllVideos(
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String cursor,
            @RequestParam(defaultValue = "20") int limit) {
        try {
            List<VideoResponse> videos = adminService.getAllVideos(status, cursor, limit);
            return ResponseEntity.ok(videos);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
    
    @GetMapping("/videos/pending")
    public ResponseEntity<List<VideoResponse>> getPendingVideos(
            @RequestParam(required = false) String cursor,
            @RequestParam(defaultValue = "20") int limit) {
        try {
            List<VideoResponse> videos = adminService.getPendingVideos(cursor, limit);
            return ResponseEntity.ok(videos);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
    
    @PostMapping("/videos/{videoId}/approve")
    public ResponseEntity<Void> approveVideo(@PathVariable String videoId) {
        try {
            UUID id = UUID.fromString(videoId);
            adminService.approveVideo(id);
            return ResponseEntity.ok().build();
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    @PostMapping("/videos/{videoId}/reject")
    public ResponseEntity<Void> rejectVideo(
            @PathVariable String videoId,
            @Valid @RequestBody RejectVideoRequest request) {
        try {
            UUID id = UUID.fromString(videoId);
            adminService.rejectVideo(id, request);
            return ResponseEntity.ok().build();
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    @DeleteMapping("/videos/{videoId}")
    public ResponseEntity<Map<String, Object>> deleteVideo(@PathVariable String videoId) {
        try {
            UUID id = UUID.fromString(videoId);
            adminService.deleteVideoAdmin(id);
            return ResponseEntity.ok(Map.of(
                "message", "Video deleted successfully",
                "video_id", videoId
            ));
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    @GetMapping("/reports")
    public ResponseEntity<Map<String, Object>> getReports(
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String cursor,
            @RequestParam(defaultValue = "20") int limit) {
        try {
            ReportStatus reportStatus = status != null ? ReportStatus.valueOf(status.toUpperCase()) : null;
            Map<String, Object> reports = adminService.getReports(reportStatus, cursor, limit);
            return ResponseEntity.ok(reports);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
    
    @PostMapping("/reports/{reportId}/resolve")
    public ResponseEntity<Map<String, Object>> resolveReport(
            Authentication authentication,
            @PathVariable String reportId,
            @Valid @RequestBody ResolveReportRequest request) {
        try {
            UUID id = UUID.fromString(reportId);
            UUID resolverId = getUserIdFromAuthentication(authentication);
            Map<String, Object> result = adminService.resolveReport(id, resolverId, request);
            return ResponseEntity.ok(result);
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().build();
        }
    }
    
    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> getAdminStats() {
        try {
            Map<String, Object> stats = analyticsService.getAdminStats();
            return ResponseEntity.ok(stats);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
    
    @GetMapping("/analytics")
    public ResponseEntity<Map<String, Object>> getAnalytics(
            @RequestParam(defaultValue = "week") String period,
            @RequestParam(defaultValue = "30") int days) {
        try {
            Map<String, Object> analytics = analyticsService.getAnalytics(period, days);
            return ResponseEntity.ok(analytics);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
    
    @GetMapping("/users")
    public ResponseEntity<Map<String, Object>> getUsers(
            @RequestParam(required = false) String cursor,
            @RequestParam(defaultValue = "50") int limit,
            @RequestParam(required = false) String search) {
        try {
            Map<String, Object> users = adminService.getUsers(cursor, limit, search);
            return ResponseEntity.ok(users);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
    
    @GetMapping("/users/{userId}")
    public ResponseEntity<Map<String, Object>> getUserDetails(@PathVariable String userId) {
        try {
            UUID id = UUID.fromString(userId);
            Map<String, Object> user = adminService.getUserDetails(id);
            return ResponseEntity.ok(user);
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    @PatchMapping("/users/{userId}")
    public ResponseEntity<Map<String, Object>> updateUser(
            @PathVariable String userId,
            @RequestBody Map<String, Object> request) {
        try {
            UUID id = UUID.fromString(userId);
            Map<String, Object> result = adminService.updateUser(id, request);
            return ResponseEntity.ok(result);
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().build();
        }
    }
    
    @GetMapping("/shares/analytics")
    public ResponseEntity<Map<String, Object>> getShareAnalytics(
            @RequestParam(defaultValue = "week") String period,
            @RequestParam(defaultValue = "30") int days,
            @RequestParam(required = false) String videoId) {
        try {
            UUID vidId = videoId != null ? UUID.fromString(videoId) : null;
            Map<String, Object> analytics = shareAnalyticsService.getShareAnalytics(period, days, vidId);
            return ResponseEntity.ok(analytics);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
    
    @GetMapping("/shares/stats")
    public ResponseEntity<Map<String, Object>> getShareStats() {
        try {
            Map<String, Object> stats = shareAnalyticsService.getShareStats();
            return ResponseEntity.ok(stats);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
    
    @GetMapping("/visitors/locations")
    public ResponseEntity<List<Map<String, Object>>> getVisitorLocations(
            @RequestParam(defaultValue = "7") int days,
            @RequestParam(defaultValue = "1") int minVisits) {
        try {
            List<Map<String, Object>> locations = visitorAnalyticsService.getVisitorLocations(days, minVisits);
            return ResponseEntity.ok(locations);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
    
    @GetMapping("/visitors/stats")
    public ResponseEntity<Map<String, Object>> getVisitorStats(
            @RequestParam(defaultValue = "30") int days) {
        try {
            Map<String, Object> stats = visitorAnalyticsService.getVisitorStats(days);
            return ResponseEntity.ok(stats);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
    
    @GetMapping("/visitors/recent")
    public ResponseEntity<List<Map<String, Object>>> getRecentVisits(
            @RequestParam(defaultValue = "100") int limit) {
        try {
            List<Map<String, Object>> visits = visitorAnalyticsService.getRecentVisits(limit);
            return ResponseEntity.ok(visits);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
    
    private UUID getUserIdFromAuthentication(Authentication authentication) {
        if (authentication == null || authentication.getPrincipal() == null) {
            throw new RuntimeException("Not authenticated");
        }
        
        UserDetails userDetails = (UserDetails) authentication.getPrincipal();
        return UUID.fromString(userDetails.getUsername());
    }
}

