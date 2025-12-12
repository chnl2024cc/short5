package com.short5.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.short5.dto.AuthResponse;
import com.short5.dto.LoginRequest;
import com.short5.dto.TokenResponse;
import com.short5.dto.UserCreateRequest;
import com.short5.exception.BadRequestException;
import com.short5.service.AuthService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.FilterType;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(
    controllers = AuthController.class,
    excludeAutoConfiguration = {
        org.springframework.boot.autoconfigure.security.servlet.SecurityAutoConfiguration.class
    },
    excludeFilters = @ComponentScan.Filter(
        type = FilterType.ASSIGNABLE_TYPE,
        classes = {
            com.short5.config.DatabaseConfig.class,
            com.short5.config.AsyncConfig.class,
            com.short5.config.RestTemplateConfig.class
        }
    )
)
@AutoConfigureMockMvc(addFilters = false)
class AuthControllerTest {
    
    @Autowired
    private MockMvc mockMvc;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    @MockBean
    private AuthService authService;
    
    // Mock security beans to prevent SecurityConfig from loading
    @MockBean
    private com.short5.security.JwtService jwtService;
    
    @MockBean
    private com.short5.security.CustomUserDetailsService userDetailsService;
    
    @MockBean
    private com.short5.security.JwtAuthenticationFilter jwtAuthenticationFilter;
    
    @Test
    void shouldRegisterUserSuccessfully() throws Exception {
        // Given
        UserCreateRequest request = new UserCreateRequest();
        request.setUsername("newuser");
        request.setEmail("newuser@example.com");
        request.setPassword("password123");
        
        AuthResponse response = AuthResponse.builder()
                .user(AuthResponse.UserResponse.builder()
                        .id(UUID.randomUUID().toString())
                        .username("newuser")
                        .email("newuser@example.com")
                        .isAdmin(false)
                        .build())
                .accessToken("access_token")
                .refreshToken("refresh_token")
                .build();
        
        when(authService.register(any(UserCreateRequest.class))).thenReturn(response);
        
        // When/Then
        mockMvc.perform(post("/api/v1/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.user.username").value("newuser"))
                .andExpect(jsonPath("$.accessToken").value("access_token"));
    }
    
    @Test
    void shouldLoginUserSuccessfully() throws Exception {
        // Given
        LoginRequest request = new LoginRequest();
        request.setEmail("test@example.com");
        request.setPassword("password123");
        
        AuthResponse response = AuthResponse.builder()
                .user(AuthResponse.UserResponse.builder()
                        .id(UUID.randomUUID().toString())
                        .username("testuser")
                        .email("test@example.com")
                        .isAdmin(false)
                        .build())
                .accessToken("access_token")
                .refreshToken("refresh_token")
                .build();
        
        when(authService.login(any(LoginRequest.class))).thenReturn(response);
        
        // When/Then
        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.user.email").value("test@example.com"))
                .andExpect(jsonPath("$.accessToken").value("access_token"));
    }
    
    @Test
    void shouldReturnConflictWhenUsernameExists() throws Exception {
        // Given
        UserCreateRequest request = new UserCreateRequest();
        request.setUsername("existinguser");
        request.setEmail("new@example.com");
        request.setPassword("password123");
        
        when(authService.register(any(UserCreateRequest.class)))
                .thenThrow(new BadRequestException("Username already exists"));
        
        // When/Then
        mockMvc.perform(post("/api/v1/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }
    
    @Test
    void shouldReturnBadRequestWhenLoginFails() throws Exception {
        // Given
        LoginRequest request = new LoginRequest();
        request.setEmail("test@example.com");
        request.setPassword("wrong_password");
        
        when(authService.login(any(LoginRequest.class)))
                .thenThrow(new BadRequestException("Invalid email or password"));
        
        // When/Then
        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }
    
    @Test
    void shouldLogoutSuccessfully() throws Exception {
        // When/Then
        mockMvc.perform(post("/api/v1/auth/logout"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("Logged out successfully"));
    }
}

