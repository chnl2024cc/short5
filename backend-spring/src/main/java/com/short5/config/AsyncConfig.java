package com.short5.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;

/**
 * Configuration for asynchronous task execution.
 * 
 * Used for:
 * - Video processing task submission (non-blocking)
 * - Background operations
 * 
 * Follows Spring Boot best practices for async configuration.
 */
@Configuration
@EnableAsync
public class AsyncConfig {
    
    /**
     * Configures thread pool for async operations.
     * 
     * Default Spring Boot auto-configuration is used, but this provides
     * explicit configuration if needed.
     * 
     * @return Executor for async tasks
     */
    @Bean(name = "taskExecutor")
    public Executor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("async-");
        executor.initialize();
        return executor;
    }
}

