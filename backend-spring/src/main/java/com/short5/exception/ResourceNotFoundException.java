package com.short5.exception;

/**
 * Exception thrown when a requested resource is not found.
 * 
 * Follows Spring Boot best practices:
 * - Custom exception for specific error cases
 * - Clear, descriptive name
 * - Extends RuntimeException (unchecked exception)
 */
public class ResourceNotFoundException extends RuntimeException {
    
    public ResourceNotFoundException(String message) {
        super(message);
    }
    
    public ResourceNotFoundException(String message, Throwable cause) {
        super(message, cause);
    }
}

