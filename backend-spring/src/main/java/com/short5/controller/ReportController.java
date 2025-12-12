package com.short5.controller;

import com.short5.dto.CreateReportRequest;
import com.short5.entity.Report;
import com.short5.security.JwtService;
import com.short5.service.ReportService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/reports")
@RequiredArgsConstructor
public class ReportController {
    
    private final ReportService reportService;
    
    @PostMapping
    public ResponseEntity<Map<String, Object>> createReport(
            Authentication authentication,
            @Valid @RequestBody CreateReportRequest request) {
        try {
            UUID reporterId = getUserIdFromAuthentication(authentication);
            Report report = reportService.createReport(reporterId, request);
            
            Map<String, Object> response = new HashMap<>();
            response.put("message", "Report submitted successfully");
            response.put("report_id", report.getId().toString());
            response.put("status", report.getStatus().name());
            
            return ResponseEntity.ok(response);
        } catch (RuntimeException e) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage());
            
            if (e.getMessage().contains("not found")) {
                return ResponseEntity.notFound().build();
            }
            return ResponseEntity.badRequest().body(error);
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

