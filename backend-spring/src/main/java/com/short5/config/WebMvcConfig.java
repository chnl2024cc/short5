package com.short5.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * Web MVC configuration for static file serving.
 * 
 * Serves uploaded videos and thumbnails from the upload directory.
 * 
 * Follows Spring Boot best practices:
 * - Static resources served from configured directory
 * - Proper path mapping
 * - Security considerations (serves only from configured directory)
 */
@Configuration
@Slf4j
public class WebMvcConfig implements WebMvcConfigurer {
    
    @Value("${file.upload-dir:/app/uploads}")
    private String uploadDir;
    
    /**
     * Configure static resource serving for uploaded videos.
     * 
     * Maps /uploads/** to the upload directory.
     * This allows videos to be accessed via:
     * - http://localhost:8080/uploads/processed/{videoId}/video.mp4
     * - http://localhost:8080/uploads/processed/{videoId}/thumbnail.jpg
     */
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // Serve processed videos and thumbnails
        registry.addResourceHandler("/uploads/**")
                .addResourceLocations("file:" + uploadDir + "/")
                .setCachePeriod(3600); // Cache for 1 hour
        
        log.info("Configured static file serving from: {}", uploadDir);
    }
}

