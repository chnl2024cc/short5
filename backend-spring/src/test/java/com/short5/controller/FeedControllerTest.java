package com.short5.controller;

import com.short5.dto.FeedResponse;
import com.short5.dto.VideoResponse;
import com.short5.service.FeedService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(FeedController.class)
class FeedControllerTest {
    
    @Autowired
    private MockMvc mockMvc;
    
    @MockBean
    private FeedService feedService;
    
    @Test
    void shouldGetFeedForAnonymousUser() throws Exception {
        // Given
        VideoResponse video = VideoResponse.builder()
                .id(UUID.randomUUID().toString())
                .title("Test Video")
                .status("READY")
                .build();
        
        FeedResponse response = FeedResponse.builder()
                .videos(List.of(video))
                .nextCursor(null)
                .hasMore(false)
                .build();
        
        when(feedService.getFeed(any(), any(), any())).thenReturn(response);
        
        // When/Then
        mockMvc.perform(get("/api/v1/feed"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.videos").isArray())
                .andExpect(jsonPath("$.videos[0].title").value("Test Video"));
    }
    
    @Test
    void shouldGetFeedWithCursor() throws Exception {
        // Given
        FeedResponse response = FeedResponse.builder()
                .videos(List.of())
                .nextCursor("2024-01-01T00:00:00Z")
                .hasMore(true)
                .build();
        
        when(feedService.getFeed(any(), any(), any())).thenReturn(response);
        
        // When/Then
        mockMvc.perform(get("/api/v1/feed")
                        .param("cursor", "2024-01-01T00:00:00Z")
                        .param("limit", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.hasMore").value(true));
    }
}

