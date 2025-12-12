package com.short5.service;

import com.short5.dto.AuthResponse;
import com.short5.dto.LoginRequest;
import com.short5.dto.UserCreateRequest;
import com.short5.entity.User;
import com.short5.entity.Vote;
import com.short5.repository.UserRepository;
import com.short5.repository.VoteRepository;
import com.short5.repository.UserLikedVideoRepository;
import com.short5.security.JwtService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.ArrayList;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {
    
    @Mock
    private UserRepository userRepository;
    
    @Mock
    private VoteRepository voteRepository;
    
    @Mock
    private UserLikedVideoRepository userLikedVideoRepository;
    
    @Mock
    private PasswordEncoder passwordEncoder;
    
    @Mock
    private JwtService jwtService;
    
    @InjectMocks
    private AuthService authService;
    
    private User testUser;
    private UUID testUserId;
    
    @BeforeEach
    void setUp() {
        testUserId = UUID.randomUUID();
        testUser = User.builder()
                .id(testUserId)
                .username("testuser")
                .email("test@example.com")
                .passwordHash("hashed_password")
                .isAdmin(false)
                .isActive(true)
                .build();
    }
    
    @Test
    void shouldRegisterUserSuccessfully() {
        // Given
        UserCreateRequest request = new UserCreateRequest();
        request.setUsername("newuser");
        request.setEmail("newuser@example.com");
        request.setPassword("password123");
        
        when(userRepository.existsByUsername("newuser")).thenReturn(false);
        when(userRepository.existsByEmail("newuser@example.com")).thenReturn(false);
        when(passwordEncoder.encode("password123")).thenReturn("hashed_password");
        when(userRepository.save(any(User.class))).thenAnswer(invocation -> {
            User user = invocation.getArgument(0);
            user.setId(UUID.randomUUID());
            return user;
        });
        when(jwtService.generateAccessToken(any(UUID.class))).thenReturn("access_token");
        when(jwtService.generateRefreshToken(any(UUID.class))).thenReturn("refresh_token");
        
        // When
        AuthResponse response = authService.register(request);
        
        // Then
        assertThat(response).isNotNull();
        assertThat(response.getUser()).isNotNull();
        assertThat(response.getUser().getUsername()).isEqualTo("newuser");
        assertThat(response.getUser().getEmail()).isEqualTo("newuser@example.com");
        assertThat(response.getAccessToken()).isEqualTo("access_token");
        assertThat(response.getRefreshToken()).isEqualTo("refresh_token");
        
        verify(userRepository).save(any(User.class));
        verify(jwtService).generateAccessToken(any(UUID.class));
        verify(jwtService).generateRefreshToken(any(UUID.class));
    }
    
    @Test
    void shouldThrowExceptionWhenUsernameExists() {
        // Given
        UserCreateRequest request = new UserCreateRequest();
        request.setUsername("existinguser");
        request.setEmail("new@example.com");
        request.setPassword("password123");
        
        when(userRepository.existsByUsername("existinguser")).thenReturn(true);
        
        // When/Then
        assertThatThrownBy(() -> authService.register(request))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("Username already exists");
        
        verify(userRepository, never()).save(any(User.class));
    }
    
    @Test
    void shouldThrowExceptionWhenEmailExists() {
        // Given
        UserCreateRequest request = new UserCreateRequest();
        request.setUsername("newuser");
        request.setEmail("existing@example.com");
        request.setPassword("password123");
        
        when(userRepository.existsByUsername("newuser")).thenReturn(false);
        when(userRepository.existsByEmail("existing@example.com")).thenReturn(true);
        
        // When/Then
        assertThatThrownBy(() -> authService.register(request))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("Email already exists");
        
        verify(userRepository, never()).save(any(User.class));
    }
    
    @Test
    void shouldLoginUserSuccessfully() {
        // Given
        LoginRequest request = new LoginRequest();
        request.setEmail("test@example.com");
        request.setPassword("password123");
        
        when(userRepository.findByEmail("test@example.com")).thenReturn(Optional.of(testUser));
        when(passwordEncoder.matches("password123", "hashed_password")).thenReturn(true);
        when(jwtService.generateAccessToken(testUserId)).thenReturn("access_token");
        when(jwtService.generateRefreshToken(testUserId)).thenReturn("refresh_token");
        
        // When
        AuthResponse response = authService.login(request);
        
        // Then
        assertThat(response).isNotNull();
        assertThat(response.getUser().getEmail()).isEqualTo("test@example.com");
        assertThat(response.getAccessToken()).isEqualTo("access_token");
        assertThat(response.getRefreshToken()).isEqualTo("refresh_token");
        
        verify(userRepository).findByEmail("test@example.com");
        verify(passwordEncoder).matches("password123", "hashed_password");
    }
    
    @Test
    void shouldThrowExceptionWhenUserNotFound() {
        // Given
        LoginRequest request = new LoginRequest();
        request.setEmail("notfound@example.com");
        request.setPassword("password123");
        
        when(userRepository.findByEmail("notfound@example.com")).thenReturn(Optional.empty());
        
        // When/Then
        assertThatThrownBy(() -> authService.login(request))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("Invalid email or password");
    }
    
    @Test
    void shouldThrowExceptionWhenPasswordIncorrect() {
        // Given
        LoginRequest request = new LoginRequest();
        request.setEmail("test@example.com");
        request.setPassword("wrong_password");
        
        when(userRepository.findByEmail("test@example.com")).thenReturn(Optional.of(testUser));
        when(passwordEncoder.matches("wrong_password", "hashed_password")).thenReturn(false);
        
        // When/Then
        assertThatThrownBy(() -> authService.login(request))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("Invalid email or password");
    }
    
    @Test
    void shouldThrowExceptionWhenUserInactive() {
        // Given
        testUser.setIsActive(false);
        LoginRequest request = new LoginRequest();
        request.setEmail("test@example.com");
        request.setPassword("password123");
        
        when(userRepository.findByEmail("test@example.com")).thenReturn(Optional.of(testUser));
        when(passwordEncoder.matches("password123", "hashed_password")).thenReturn(true);
        
        // When/Then
        assertThatThrownBy(() -> authService.login(request))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("User account is inactive");
    }
    
    @Test
    void shouldMergeAnonymousVotesOnRegistration() {
        // Given
        UserCreateRequest request = new UserCreateRequest();
        request.setUsername("newuser");
        request.setEmail("newuser@example.com");
        request.setPassword("password123");
        UUID sessionId = UUID.randomUUID();
        request.setSessionId(sessionId.toString());
        
        Vote anonymousVote = Vote.builder()
                .id(UUID.randomUUID())
                .sessionId(sessionId)
                .videoId(UUID.randomUUID())
                .direction(Vote.VoteDirection.LIKE)
                .build();
        
        when(userRepository.existsByUsername("newuser")).thenReturn(false);
        when(userRepository.existsByEmail("newuser@example.com")).thenReturn(false);
        when(passwordEncoder.encode("password123")).thenReturn("hashed_password");
        when(userRepository.save(any(User.class))).thenAnswer(invocation -> {
            User user = invocation.getArgument(0);
            user.setId(testUserId);
            return user;
        });
        when(jwtService.generateAccessToken(any(UUID.class))).thenReturn("access_token");
        when(jwtService.generateRefreshToken(any(UUID.class))).thenReturn("refresh_token");
        when(voteRepository.findAllBySessionId(sessionId)).thenReturn(java.util.List.of(anonymousVote));
        when(voteRepository.findByUserIdAndVideoId(any(UUID.class), any(UUID.class)))
                .thenReturn(Optional.empty());
        when(userLikedVideoRepository.existsByUserIdAndVideoId(any(UUID.class), any(UUID.class)))
                .thenReturn(false);
        
        // When
        AuthResponse response = authService.register(request);
        
        // Then
        assertThat(response).isNotNull();
        verify(voteRepository).findAllBySessionId(sessionId);
        verify(voteRepository).save(any(Vote.class));
    }
}

