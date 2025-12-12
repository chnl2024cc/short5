package com.short5.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class ViewRequest {
    @NotNull(message = "Watched seconds is required")
    @Min(value = 0, message = "Watched seconds must be >= 0")
    private Integer watchedSeconds;
}

