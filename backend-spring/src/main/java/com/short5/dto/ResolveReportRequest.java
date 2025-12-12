package com.short5.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ResolveReportRequest {
    @NotBlank(message = "Action is required")
    private String action; // "resolve" or "dismiss"
    
    private String notes;
}

