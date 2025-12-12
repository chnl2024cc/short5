package com.short5.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * Web MVC configuration.
 * 
 * Note: Resource handler registration for /uploads/** is handled by FileStorageConfig
 * to avoid duplicate registrations. This class is kept for potential
 * future WebMvcConfigurer customizations.
 */
@Configuration
public class WebMvcConfig implements WebMvcConfigurer {
    // Resource handler registration moved to FileStorageConfig to avoid duplication
}

