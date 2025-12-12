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

/**
 * Global exception handler for all controllers.
 * 
 * Follows Spring Boot best practices:
 * - Centralized exception handling
 * - Proper HTTP status codes
 * - Consistent error response format
 * - Does not expose internal errors to clients
 */
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {
    
    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<Map<String, Object>> handleResourceNotFound(ResourceNotFoundException e) {
        log.warn("Resource not found: {}", e.getMessage());
        
        Map<String, Object> error = new HashMap<>();
        error.put("error", Map.of(
                "code", "RESOURCE_NOT_FOUND",
                "message", e.getMessage()
        ));
        
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
    }
    
    @ExceptionHandler(BadRequestException.class)
    public ResponseEntity<Map<String, Object>> handleBadRequest(BadRequestException e) {
        log.warn("Bad request: {}", e.getMessage());
        
        Map<String, Object> error = new HashMap<>();
        error.put("error", Map.of(
                "code", "BAD_REQUEST",
                "message", e.getMessage()
        ));
        
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }
    
    @ExceptionHandler(ForbiddenException.class)
    public ResponseEntity<Map<String, Object>> handleForbidden(ForbiddenException e) {
        log.warn("Forbidden: {}", e.getMessage());
        
        Map<String, Object> error = new HashMap<>();
        error.put("error", Map.of(
                "code", "FORBIDDEN",
                "message", e.getMessage()
        ));
        
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(error);
    }
    
    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<Map<String, Object>> handleRuntimeException(RuntimeException e) {
        // Check if it's a known exception type that should be handled differently
        if (e instanceof ResourceNotFoundException) {
            return handleResourceNotFound((ResourceNotFoundException) e);
        }
        if (e instanceof BadRequestException) {
            return handleBadRequest((BadRequestException) e);
        }
        if (e instanceof ForbiddenException) {
            return handleForbidden((ForbiddenException) e);
        }
        
        log.error("Runtime exception: {}", e.getMessage(), e);
        
        Map<String, Object> error = new HashMap<>();
        error.put("error", Map.of(
                "code", "RUNTIME_ERROR",
                "message", e.getMessage()
        ));
        
        HttpStatus status = HttpStatus.INTERNAL_SERVER_ERROR;
        if (e.getMessage() != null) {
            String message = e.getMessage().toLowerCase();
            if (message.contains("not found")) {
                status = HttpStatus.NOT_FOUND;
            } else if (message.contains("already exists") || message.contains("already reported")) {
                status = HttpStatus.CONFLICT;
            } else if (message.contains("not authorized") || message.contains("cannot report")) {
                status = HttpStatus.FORBIDDEN;
            } else if (message.contains("invalid") || message.contains("required")) {
                status = HttpStatus.BAD_REQUEST;
            }
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

