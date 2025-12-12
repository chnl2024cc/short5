package com.short5.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.short5.security.CustomUserDetailsService;
import com.short5.security.JwtAuthenticationFilter;
import com.short5.security.JwtService;
import com.short5.service.VideoProcessingService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.FilterType;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.verify;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(
    controllers = InternalController.class,
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
class InternalControllerTest {
    
    @Autowired
    private MockMvc mockMvc;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    @MockBean
    private VideoProcessingService videoProcessingService;
    
    // Mock security beans
    @MockBean
    private com.short5.security.JwtService jwtService;
    
    @MockBean
    private com.short5.security.CustomUserDetailsService userDetailsService;
    
    @MockBean
    private com.short5.security.JwtAuthenticationFilter jwtAuthenticationFilter;
    
    private UUID testVideoId = UUID.randomUUID();
    
    @Test
    void shouldHandleProcessingCompleteSuccessfully() throws Exception {
        // Given
        Map<String, Object> processingResult = new HashMap<>();
        processingResult.put("success", true);
        processingResult.put("url_mp4", "http://example.com/video.mp4");
        processingResult.put("thumbnail", "http://example.com/thumb.jpg");
        processingResult.put("duration_seconds", 120);
        
        doNothing().when(videoProcessingService).handleProcessingComplete(
                eq(testVideoId), any(Map.class));
        
        // When/Then
        mockMvc.perform(post("/api/v1/internal/videos/{videoId}/processing-complete", testVideoId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(processingResult)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("success"))
                .andExpect(jsonPath("$.message").value("Processing result received"));
        
        verify(videoProcessingService).handleProcessingComplete(eq(testVideoId), any(Map.class));
    }
    
    @Test
    void shouldHandleProcessingCompleteWithError() throws Exception {
        // Given
        Map<String, Object> processingResult = new HashMap<>();
        processingResult.put("success", false);
        processingResult.put("error", "Processing failed");
        
        doNothing().when(videoProcessingService).handleProcessingComplete(
                eq(testVideoId), any(Map.class));
        
        // When/Then
        mockMvc.perform(post("/api/v1/internal/videos/{videoId}/processing-complete", testVideoId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(processingResult)))
                .andExpect(status().isOk()); // Service handles the error internally
        
        verify(videoProcessingService).handleProcessingComplete(eq(testVideoId), any(Map.class));
    }
    
    @Test
    void shouldHandleInvalidVideoId() throws Exception {
        // Given
        Map<String, Object> processingResult = new HashMap<>();
        processingResult.put("success", true);
        
        // When invalid UUID format
        mockMvc.perform(post("/api/v1/internal/videos/{videoId}/processing-complete", "invalid-uuid")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(processingResult)))
                .andExpect(status().isBadRequest());
    }
}

