package com.short5.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.transaction.annotation.EnableTransactionManagement;

/**
 * Database Configuration
 * 
 * Enables JPA auditing and transaction management.
 * Database connection is configured via application.yml
 */
@Configuration
@EnableJpaAuditing
@EnableTransactionManagement
public class DatabaseConfig {
    // Configuration is handled via application.yml
}

