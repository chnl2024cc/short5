package com.short5.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ShareClickRequest {
    @NotBlank(message = "Sharer session ID is required")
    private String sharerSessionId;
    
    @NotBlank(message = "Clicker session ID is required")
    private String clickerSessionId;
}

