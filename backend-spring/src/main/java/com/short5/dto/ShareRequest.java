package com.short5.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ShareRequest {
    @NotBlank(message = "Sharer session ID is required")
    private String sharerSessionId;
}

