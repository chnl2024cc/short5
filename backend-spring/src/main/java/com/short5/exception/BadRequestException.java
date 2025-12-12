package com.short5.exception;

/**
 * Exception thrown when a request is invalid or malformed.
 * 
 * Follows Spring Boot best practices:
 * - Custom exception for specific error cases
 * - Clear, descriptive name
 * - Extends RuntimeException (unchecked exception)
 */
public class BadRequestException extends RuntimeException {
    
    public BadRequestException(String message) {
        super(message);
    }
    
    public BadRequestException(String message, Throwable cause) {
        super(message, cause);
    }
}

