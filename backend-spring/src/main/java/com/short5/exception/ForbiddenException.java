package com.short5.exception;

/**
 * Exception thrown when access is forbidden (authorization failure).
 * 
 * Follows Spring Boot best practices:
 * - Custom exception for specific error cases
 * - Clear, descriptive name
 * - Extends RuntimeException (unchecked exception)
 */
public class ForbiddenException extends RuntimeException {
    
    public ForbiddenException(String message) {
        super(message);
    }
    
    public ForbiddenException(String message, Throwable cause) {
        super(message, cause);
    }
}

