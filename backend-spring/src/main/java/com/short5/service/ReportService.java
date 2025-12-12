package com.short5.service;

import com.short5.dto.CreateReportRequest;
import com.short5.entity.Report;
import com.short5.entity.Report.ReportType;
import com.short5.entity.Report.ReportStatus;
import com.short5.entity.User;
import com.short5.entity.Video;
import com.short5.repository.ReportRepository;
import com.short5.repository.UserRepository;
import com.short5.repository.VideoRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class ReportService {
    
    private final ReportRepository reportRepository;
    private final UserRepository userRepository;
    private final VideoRepository videoRepository;
    
    @Transactional
    public Report createReport(UUID reporterId, CreateReportRequest request) {
        // Validate report type
        ReportType reportType;
        try {
            reportType = request.getReportType();
        } catch (IllegalArgumentException e) {
            throw new RuntimeException("Invalid report_type. Must be 'VIDEO' or 'USER'");
        }
        
        UUID targetId = UUID.fromString(request.getTargetId());
        
        // Validate target exists
        if (reportType == ReportType.VIDEO) {
            Video video = videoRepository.findById(targetId)
                    .orElseThrow(() -> new RuntimeException("Video not found"));
            
            // Prevent reporting own video
            if (video.getUserId().equals(reporterId)) {
                throw new RuntimeException("Cannot report your own video");
            }
        } else {
            User targetUser = userRepository.findById(targetId)
                    .orElseThrow(() -> new RuntimeException("User not found"));
            
            // Prevent reporting yourself
            if (targetUser.getId().equals(reporterId)) {
                throw new RuntimeException("Cannot report yourself");
            }
        }
        
        // Check if user already reported this target
        boolean alreadyReported = reportRepository.findByReporterId(reporterId).stream()
                .anyMatch(report -> report.getReportType() == reportType && report.getTargetId().equals(targetId));
        
        if (alreadyReported) {
            throw new RuntimeException("You have already reported this " + reportType.name().toLowerCase());
        }
        
        // Create report
        Report report = Report.builder()
                .reporterId(reporterId)
                .reportType(reportType)
                .targetId(targetId)
                .reason(request.getReason())
                .status(ReportStatus.PENDING)
                .build();
        
        return reportRepository.save(report);
    }
}

