package com.short5;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.scheduling.annotation.EnableAsync;

/**
 * Main Spring Boot Application
 * 
 * This is an alternative backend implementation for Short5 Platform.
 * It can run alongside or replace the FastAPI backend.
 * 
 * Uses the same database, Redis, and video_worker services.
 */
@SpringBootApplication
@EnableJpaRepositories(basePackages = "com.short5.repository")
@EntityScan(basePackages = "com.short5.entity")
@EnableAsync
public class Short5Application {

    public static void main(String[] args) {
        SpringApplication.run(Short5Application.class, args);
    }
}

