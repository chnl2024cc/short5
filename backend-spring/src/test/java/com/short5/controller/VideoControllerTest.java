package com.short5.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.short5.dto.*;
import com.short5.service.VideoService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(VideoController.class)
class VideoControllerTest {
    
    @Autowired
    private MockMvc mockMvc;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    @MockBean
    private VideoService videoService;
    
    private UUID testVideoId = UUID.randomUUID();
    
    @Test
    void shouldGetVideoSuccessfully() throws Exception {
        // Given
        VideoResponse response = VideoResponse.builder()
                .id(testVideoId.toString())
                .title("Test Video")
                .status("READY")
                .urlMp4("http://example.com/video.mp4")
                .build();
        
        when(videoService.getVideo(testVideoId)).thenReturn(response);
        
        // When/Then
        mockMvc.perform(get("/api/v1/videos/{videoId}", testVideoId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(testVideoId.toString()))
                .andExpect(jsonPath("$.title").value("Test Video"));
    }
    
    @Test
    @WithMockUser
    void shouldUploadVideoSuccessfully() throws Exception {
        // Given
        MockMultipartFile file = new MockMultipartFile(
                "file", "test.mp4", "video/mp4", "test content".getBytes());
        
        VideoResponse response = VideoResponse.builder()
                .id(testVideoId.toString())
                .title("Test Video")
                .status("PROCESSING")
                .build();
        
        when(videoService.uploadVideo(any(UUID.class), any(), any(), any()))
                .thenReturn(response);
        
        // When/Then
        mockMvc.perform(multipart("/api/v1/videos/upload")
                        .file(file)
                        .param("title", "Test Video")
                        .with(csrf()))
                .andExpect(status().isAccepted());
    }
    
    @Test
    @WithMockUser
    void shouldVoteOnVideoSuccessfully() throws Exception {
        // Given
        VoteRequest request = new VoteRequest();
        request.setDirection("like");
        
        VoteResponse response = VoteResponse.builder()
                .message("Vote recorded")
                .videoId(testVideoId.toString())
                .direction("like")
                .build();
        
        when(videoService.voteOnVideo(eq(testVideoId), any(VoteRequest.class), any(), any()))
                .thenReturn(response);
        
        // When/Then
        mockMvc.perform(post("/api/v1/videos/{videoId}/vote", testVideoId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request))
                        .with(csrf()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.direction").value("like"));
    }
    
    @Test
    @WithMockUser
    void shouldRecordViewSuccessfully() throws Exception {
        // Given
        ViewRequest request = new ViewRequest();
        request.setWatchedSeconds(30);
        
        ViewResponse response = ViewResponse.builder()
                .message("View recorded")
                .build();
        
        when(videoService.recordView(eq(testVideoId), any(ViewRequest.class), any()))
                .thenReturn(response);
        
        // When/Then
        mockMvc.perform(post("/api/v1/videos/{videoId}/view", testVideoId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request))
                        .with(csrf()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("View recorded"));
    }
    
    @Test
    @WithMockUser
    void shouldDeleteVideoSuccessfully() throws Exception {
        // When/Then
        mockMvc.perform(delete("/api/v1/videos/{videoId}", testVideoId)
                        .with(csrf()))
                .andExpect(status().isNoContent());
        
        // Verify service was called
        // (In a real test, you'd verify the service method was called)
    }
}

