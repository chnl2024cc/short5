package com.short5.security;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

@ExtendWith(MockitoExtension.class)
class JwtServiceTest {
    
    @InjectMocks
    private JwtService jwtService;
    
    private static final String TEST_SECRET = "test-secret-key-that-is-long-enough-for-hmac-sha256-algorithm";
    private UUID testUserId;
    
    @BeforeEach
    void setUp() {
        testUserId = UUID.randomUUID();
        
        // Set test secret
        ReflectionTestUtils.setField(jwtService, "secret", TEST_SECRET);
        ReflectionTestUtils.setField(jwtService, "algorithm", "HS256");
        ReflectionTestUtils.setField(jwtService, "accessTokenExpireMinutes", 30);
        ReflectionTestUtils.setField(jwtService, "refreshTokenExpireDays", 7);
    }
    
    @Test
    void shouldGenerateAccessToken() {
        // When
        String token = jwtService.generateAccessToken(testUserId);
        
        // Then
        assertThat(token).isNotNull();
        assertThat(token).isNotEmpty();
    }
    
    @Test
    void shouldGenerateRefreshToken() {
        // When
        String token = jwtService.generateRefreshToken(testUserId);
        
        // Then
        assertThat(token).isNotNull();
        assertThat(token).isNotEmpty();
    }
    
    @Test
    void shouldExtractUserIdFromToken() {
        // Given
        String token = jwtService.generateAccessToken(testUserId);
        
        // When
        String extractedUserId = jwtService.extractUserId(token);
        
        // Then
        assertThat(extractedUserId).isEqualTo(testUserId.toString());
    }
    
    @Test
    void shouldValidateAccessToken() {
        // Given
        String token = jwtService.generateAccessToken(testUserId);
        
        // When
        Boolean isValid = jwtService.validateAccessToken(token);
        
        // Then
        assertThat(isValid).isTrue();
    }
    
    @Test
    void shouldValidateRefreshToken() {
        // Given
        String token = jwtService.generateRefreshToken(testUserId);
        
        // When
        Boolean isValid = jwtService.validateRefreshToken(token);
        
        // Then
        assertThat(isValid).isTrue();
    }
    
    @Test
    void shouldExtractTokenType() {
        // Given
        String accessToken = jwtService.generateAccessToken(testUserId);
        String refreshToken = jwtService.generateRefreshToken(testUserId);
        
        // When
        String accessType = jwtService.extractTokenType(accessToken);
        String refreshType = jwtService.extractTokenType(refreshToken);
        
        // Then
        assertThat(accessType).isEqualTo("access");
        assertThat(refreshType).isEqualTo("refresh");
    }
    
    @Test
    void shouldRejectInvalidToken() {
        // Given
        String invalidToken = "invalid.token.here";
        
        // When
        Boolean isValid = jwtService.validateAccessToken(invalidToken);
        
        // Then
        assertThat(isValid).isFalse();
    }
}

