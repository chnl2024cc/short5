package com.short5.service;

import com.short5.dto.CreateReportRequest;
import com.short5.entity.Report;
import com.short5.entity.Report.ReportType;
import com.short5.entity.User;
import com.short5.entity.Video;
import com.short5.repository.ReportRepository;
import com.short5.repository.UserRepository;
import com.short5.repository.VideoRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ReportServiceTest {
    
    @Mock
    private ReportRepository reportRepository;
    
    @Mock
    private UserRepository userRepository;
    
    @Mock
    private VideoRepository videoRepository;
    
    @InjectMocks
    private ReportService reportService;
    
    private User reporter;
    private User targetUser;
    private Video targetVideo;
    private UUID reporterId;
    private UUID targetUserId;
    private UUID targetVideoId;
    
    @BeforeEach
    void setUp() {
        reporterId = UUID.randomUUID();
        reporter = User.builder()
                .id(reporterId)
                .username("reporter")
                .email("reporter@example.com")
                .build();
        
        targetUserId = UUID.randomUUID();
        targetUser = User.builder()
                .id(targetUserId)
                .username("targetuser")
                .email("target@example.com")
                .build();
        
        targetVideoId = UUID.randomUUID();
        targetVideo = Video.builder()
                .id(targetVideoId)
                .userId(targetUserId)
                .title("Target Video")
                .build();
    }
    
    @Test
    void shouldCreateVideoReportSuccessfully() {
        // Given
        CreateReportRequest request = new CreateReportRequest();
        request.setReportType(ReportType.VIDEO);
        request.setTargetId(targetVideoId.toString());
        request.setReason("Inappropriate content");
        
        when(videoRepository.findById(targetVideoId)).thenReturn(Optional.of(targetVideo));
        when(reportRepository.findByReporterId(reporterId)).thenReturn(List.of());
        when(reportRepository.save(any(Report.class))).thenAnswer(invocation -> invocation.getArgument(0));
        
        // When
        Report report = reportService.createReport(reporterId, request);
        
        // Then
        assertThat(report).isNotNull();
        assertThat(report.getReportType()).isEqualTo(ReportType.VIDEO);
        assertThat(report.getTargetId()).isEqualTo(targetVideoId);
        assertThat(report.getReporterId()).isEqualTo(reporterId);
        
        verify(reportRepository).save(any(Report.class));
    }
    
    @Test
    void shouldCreateUserReportSuccessfully() {
        // Given
        CreateReportRequest request = new CreateReportRequest();
        request.setReportType(ReportType.USER);
        request.setTargetId(targetUserId.toString());
        request.setReason("Spam account");
        
        when(userRepository.findById(targetUserId)).thenReturn(Optional.of(targetUser));
        when(reportRepository.findByReporterId(reporterId)).thenReturn(List.of());
        when(reportRepository.save(any(Report.class))).thenAnswer(invocation -> invocation.getArgument(0));
        
        // When
        Report report = reportService.createReport(reporterId, request);
        
        // Then
        assertThat(report).isNotNull();
        assertThat(report.getReportType()).isEqualTo(ReportType.USER);
        assertThat(report.getTargetId()).isEqualTo(targetUserId);
        
        verify(reportRepository).save(any(Report.class));
    }
    
    @Test
    void shouldThrowExceptionWhenTargetNotFound() {
        // Given
        CreateReportRequest request = new CreateReportRequest();
        request.setReportType(ReportType.VIDEO);
        request.setTargetId(UUID.randomUUID().toString());
        
        when(videoRepository.findById(any(UUID.class))).thenReturn(Optional.empty());
        
        // When/Then
        assertThatThrownBy(() -> reportService.createReport(reporterId, request))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("Video not found");
    }
    
    @Test
    void shouldThrowExceptionWhenReportingOwnVideo() {
        // Given
        targetVideo.setUserId(reporterId); // Reporter owns the video
        CreateReportRequest request = new CreateReportRequest();
        request.setReportType(ReportType.VIDEO);
        request.setTargetId(targetVideoId.toString());
        
        when(videoRepository.findById(targetVideoId)).thenReturn(Optional.of(targetVideo));
        
        // When/Then
        assertThatThrownBy(() -> reportService.createReport(reporterId, request))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("Cannot report your own video");
    }
    
    @Test
    void shouldThrowExceptionWhenAlreadyReported() {
        // Given
        CreateReportRequest request = new CreateReportRequest();
        request.setReportType(ReportType.VIDEO);
        request.setTargetId(targetVideoId.toString());
        
        Report existingReport = Report.builder()
                .id(UUID.randomUUID())
                .reporterId(reporterId)
                .reportType(ReportType.VIDEO)
                .targetId(targetVideoId)
                .build();
        
        when(videoRepository.findById(targetVideoId)).thenReturn(Optional.of(targetVideo));
        when(reportRepository.findByReporterId(reporterId)).thenReturn(List.of(existingReport));
        
        // When/Then
        assertThatThrownBy(() -> reportService.createReport(reporterId, request))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("already reported");
    }
}

