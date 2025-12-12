package com.short5.exception;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.HashMap;
import java.util.Map;

@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {
    
    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<Map<String, Object>> handleRuntimeException(RuntimeException e) {
        log.error("Runtime exception: {}", e.getMessage(), e);
        
        Map<String, Object> error = new HashMap<>();
        error.put("error", Map.of(
                "code", "RUNTIME_ERROR",
                "message", e.getMessage()
        ));
        
        HttpStatus status = HttpStatus.INTERNAL_SERVER_ERROR;
        if (e.getMessage().contains("not found")) {
            status = HttpStatus.NOT_FOUND;
        } else if (e.getMessage().contains("already exists") || 
                   e.getMessage().contains("already reported")) {
            status = HttpStatus.CONFLICT;
        } else if (e.getMessage().contains("Not authorized") || 
                   e.getMessage().contains("Cannot report")) {
            status = HttpStatus.FORBIDDEN;
        } else if (e.getMessage().contains("Invalid") || 
                   e.getMessage().contains("required")) {
            status = HttpStatus.BAD_REQUEST;
        }
        
        return ResponseEntity.status(status).body(error);
    }
    
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> handleValidationException(MethodArgumentNotValidException e) {
        Map<String, String> errors = new HashMap<>();
        e.getBindingResult().getAllErrors().forEach(error -> {
            String fieldName = ((FieldError) error).getField();
            String errorMessage = error.getDefaultMessage();
            errors.put(fieldName, errorMessage);
        });
        
        Map<String, Object> error = new HashMap<>();
        error.put("error", Map.of(
                "code", "VALIDATION_ERROR",
                "message", "Validation failed",
                "details", errors
        ));
        
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }
    
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleGenericException(Exception e) {
        log.error("Unexpected exception: {}", e.getMessage(), e);
        
        Map<String, Object> error = new HashMap<>();
        error.put("error", Map.of(
                "code", "INTERNAL_ERROR",
                "message", "An unexpected error occurred"
        ));
        
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }
}

