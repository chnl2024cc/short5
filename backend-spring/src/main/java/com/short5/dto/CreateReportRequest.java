package com.short5.dto;

import com.short5.entity.Report;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class CreateReportRequest {
    @NotNull(message = "Report type is required")
    private Report.ReportType reportType;
    
    @NotBlank(message = "Target ID is required")
    private String targetId;
    
    private String reason;
}

