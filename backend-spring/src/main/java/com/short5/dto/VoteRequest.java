package com.short5.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

@Data
public class VoteRequest {
    @NotBlank(message = "Direction is required")
    @Pattern(regexp = "^(like|not_like)$", message = "Direction must be 'like' or 'not_like'")
    private String direction;
    
    private String sessionId; // For anonymous votes
}

