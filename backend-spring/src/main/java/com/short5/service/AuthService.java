package com.short5.service;

import com.short5.dto.*;
import com.short5.entity.User;
import com.short5.entity.Vote;
import com.short5.entity.UserLikedVideo;
import com.short5.entity.Vote.VoteDirection;
import com.short5.repository.UserRepository;
import com.short5.repository.VoteRepository;
import com.short5.repository.UserLikedVideoRepository;
import com.short5.security.JwtService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class AuthService {
    
    private final UserRepository userRepository;
    private final VoteRepository voteRepository;
    private final UserLikedVideoRepository userLikedVideoRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    
    @Transactional
    public AuthResponse register(UserCreateRequest request) {
        // Check if username exists
        if (userRepository.existsByUsername(request.getUsername())) {
            throw new RuntimeException("Username already exists");
        }
        
        // Check if email exists
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new RuntimeException("Email already exists");
        }
        
        // Create user
        User user = User.builder()
                .username(request.getUsername())
                .email(request.getEmail())
                .passwordHash(passwordEncoder.encode(request.getPassword()))
                .isAdmin(false)
                .isActive(true)
                .build();
        
        user = userRepository.save(user);
        
        // Create tokens
        String accessToken = jwtService.generateAccessToken(user.getId());
        String refreshToken = jwtService.generateRefreshToken(user.getId());
        
        // Merge anonymous votes if session_id provided
        if (request.getSessionId() != null && !request.getSessionId().isEmpty()) {
            try {
                UUID sessionId = UUID.fromString(request.getSessionId());
                mergeAnonymousVotes(user.getId(), sessionId);
            } catch (IllegalArgumentException e) {
                log.warn("Invalid session_id format: {}", request.getSessionId());
            }
        }
        
        return AuthResponse.builder()
                .user(AuthResponse.UserResponse.builder()
                        .id(user.getId().toString())
                        .username(user.getUsername())
                        .email(user.getEmail())
                        .isAdmin(user.getIsAdmin())
                        .createdAt(user.getCreatedAt())
                        .build())
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .build();
    }
    
    @Transactional
    public AuthResponse login(LoginRequest request) {
        // Find user by email
        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new RuntimeException("Invalid email or password"));
        
        // Verify password
        if (!passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
            throw new RuntimeException("Invalid email or password");
        }
        
        // Check if user is active
        if (!user.getIsActive()) {
            throw new RuntimeException("User account is inactive");
        }
        
        // Create tokens
        String accessToken = jwtService.generateAccessToken(user.getId());
        String refreshToken = jwtService.generateRefreshToken(user.getId());
        
        // Merge anonymous votes if session_id provided
        if (request.getSessionId() != null && !request.getSessionId().isEmpty()) {
            try {
                UUID sessionId = UUID.fromString(request.getSessionId());
                mergeAnonymousVotes(user.getId(), sessionId);
            } catch (IllegalArgumentException e) {
                log.warn("Invalid session_id format: {}", request.getSessionId());
            }
        }
        
        return AuthResponse.builder()
                .user(AuthResponse.UserResponse.builder()
                        .id(user.getId().toString())
                        .username(user.getUsername())
                        .email(user.getEmail())
                        .isAdmin(user.getIsAdmin())
                        .createdAt(user.getCreatedAt())
                        .build())
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .build();
    }
    
    @Transactional
    public TokenResponse refreshToken(RefreshTokenRequest request) {
        // Validate refresh token
        if (!jwtService.validateRefreshToken(request.getRefreshToken())) {
            throw new RuntimeException("Invalid refresh token");
        }
        
        // Extract user ID from token
        String userIdStr = jwtService.extractUserId(request.getRefreshToken());
        UUID userId = UUID.fromString(userIdStr);
        
        // Verify user exists and is active
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));
        
        if (!user.getIsActive()) {
            throw new RuntimeException("User account is inactive");
        }
        
        // Generate new tokens
        String accessToken = jwtService.generateAccessToken(user.getId());
        String refreshToken = jwtService.generateRefreshToken(user.getId());
        
        return TokenResponse.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .tokenType("bearer")
                .build();
    }
    
    @Transactional
    private int mergeAnonymousVotes(UUID userId, UUID sessionId) {
        // Find all anonymous votes with this session_id
        List<Vote> anonymousVotes = voteRepository.findAllBySessionId(sessionId);
        
        if (anonymousVotes.isEmpty()) {
            return 0;
        }
        
        int mergedCount = 0;
        
        for (Vote anonymousVote : anonymousVotes) {
            // Check if user already voted on this video
            Optional<Vote> existingVote = voteRepository.findByUserIdAndVideoId(userId, anonymousVote.getVideoId());
            
            if (existingVote.isPresent()) {
                // User already voted - keep the authenticated vote, delete anonymous one
                voteRepository.delete(anonymousVote);
            } else {
                // No existing vote - transfer anonymous vote to user
                anonymousVote.setUserId(userId);
                anonymousVote.setSessionId(null);
                voteRepository.save(anonymousVote);
                
                // If it was a like, also add to UserLikedVideo
                if (anonymousVote.getDirection() == VoteDirection.LIKE) {
                    if (!userLikedVideoRepository.existsByUserIdAndVideoId(userId, anonymousVote.getVideoId())) {
                        UserLikedVideo likedVideo = UserLikedVideo.builder()
                                .userId(userId)
                                .videoId(anonymousVote.getVideoId())
                                .build();
                        userLikedVideoRepository.save(likedVideo);
                    }
                }
                
                mergedCount++;
            }
        }
        
        log.info("Merged {} anonymous votes for user {}", mergedCount, userId);
        return mergedCount;
    }
}

