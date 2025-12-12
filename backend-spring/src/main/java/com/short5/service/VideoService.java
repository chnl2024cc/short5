package com.short5.service;

import com.short5.dto.*;
import com.short5.entity.*;
import com.short5.entity.Video.VideoStatus;
import com.short5.entity.Vote.VoteDirection;
import com.short5.exception.BadRequestException;
import com.short5.exception.ForbiddenException;
import com.short5.exception.ResourceNotFoundException;
import com.short5.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class VideoService {
    
    private final VideoRepository videoRepository;
    private final UserRepository userRepository;
    private final VoteRepository voteRepository;
    private final ViewRepository viewRepository;
    private final UserLikedVideoRepository userLikedVideoRepository;
    private final ShareLinkRepository shareLinkRepository;
    private final ShareClickRepository shareClickRepository;
    private final VideoProcessingService videoProcessingService;
    
    @Value("${file.upload-dir:/app/uploads}")
    private String uploadDir;
    
    @Transactional(readOnly = true)
    public VideoResponse getVideo(UUID videoId) {
        Video video = videoRepository.findById(videoId)
                .orElseThrow(() -> new ResourceNotFoundException("Video not found: " + videoId));
        
        User user = video.getUser();
        if (user == null) {
            user = userRepository.findById(video.getUserId())
                    .orElseThrow(() -> new RuntimeException("User not found"));
        }
        
        long likes = voteRepository.countByVideoIdAndDirection(videoId, VoteDirection.LIKE);
        long notLikes = voteRepository.countByVideoIdAndDirection(videoId, VoteDirection.NOT_LIKE);
        long views = viewRepository.countByVideoId(videoId);
        
        return VideoResponse.builder()
                .id(video.getId().toString())
                .title(video.getTitle())
                .description(video.getDescription())
                .status(video.getStatus().name())
                .thumbnail(video.getThumbnail())
                .urlMp4(video.getUrlMp4())
                .durationSeconds(video.getDurationSeconds())
                .errorReason(video.getErrorReason())
                .user(VideoResponse.UserBasic.builder()
                        .id(user.getId().toString())
                        .username(user.getUsername())
                        .build())
                .stats(VideoResponse.VideoStats.builder()
                        .likes(likes)
                        .notLikes(notLikes)
                        .views(views)
                        .build())
                .createdAt(video.getCreatedAt())
                .build();
    }
    
    @Transactional
    public VideoResponse uploadVideo(UUID userId, MultipartFile file, String title, String description) throws IOException {
        // Validate file extension
        String filename = file.getOriginalFilename();
        if (filename == null) {
            throw new BadRequestException("Filename is required");
        }
        
        String fileExt = filename.substring(filename.lastIndexOf('.')).toLowerCase();
        List<String> allowedFormats = List.of(".mp4", ".mov", ".avi");
        if (!allowedFormats.contains(fileExt)) {
            throw new BadRequestException("Invalid file format. Allowed: " + String.join(", ", allowedFormats));
        }
        
        // Validate file size (500MB max)
        long fileSize = file.getSize();
        long maxSize = 500 * 1024 * 1024; // 500MB
        if (fileSize > maxSize) {
            throw new BadRequestException("File too large. Max size: 500MB");
        }
        
        // Create video record
        Video video = Video.builder()
                .userId(userId)
                .title(title != null && !title.isEmpty() ? title : filename.substring(0, filename.lastIndexOf('.')))
                .description(description)
                .status(VideoStatus.UPLOADING)
                .fileSizeBytes(java.math.BigInteger.valueOf(fileSize))
                .originalFilename(filename)
                .build();
        
        video = videoRepository.save(video);
        
        // Save original file
        Path uploadPath = Paths.get(uploadDir);
        Path originalsDir = uploadPath.resolve("originals");
        Files.createDirectories(originalsDir);
        
        String videoFilename = video.getId() + fileExt;
        Path filePath = originalsDir.resolve(videoFilename);
        Files.write(filePath, file.getBytes());
        
        // Update video status to PROCESSING
        video.setStatus(VideoStatus.PROCESSING);
        video = videoRepository.save(video);
        
        // Trigger video processing task asynchronously
        videoProcessingService.triggerVideoProcessing(video.getId());
        log.info("Video {} uploaded, processing task triggered", video.getId());
        
        return getVideo(video.getId());
    }
    
    @Transactional
    public void deleteVideo(UUID videoId, UUID userId) {
        Video video = videoRepository.findById(videoId)
                .orElseThrow(() -> new ResourceNotFoundException("Video not found: " + videoId));
        
        // Check ownership
        if (!video.getUserId().equals(userId)) {
            throw new ForbiddenException("Not authorized to delete this video");
        }
        
        // Delete files
        try {
            Path uploadPath = Paths.get(uploadDir);
            
            // Delete original file
            String originalExt = video.getOriginalFilename() != null 
                    ? video.getOriginalFilename().substring(video.getOriginalFilename().lastIndexOf('.'))
                    : ".mp4";
            Path originalFile = uploadPath.resolve("originals").resolve(video.getId() + originalExt);
            Files.deleteIfExists(originalFile);
            
            // Delete processed files
            Path processedDir = uploadPath.resolve("processed").resolve(video.getId().toString());
            if (Files.exists(processedDir)) {
                Files.walk(processedDir)
                        .sorted((a, b) -> -a.compareTo(b))
                        .forEach(path -> {
                            try {
                                Files.delete(path);
                            } catch (IOException e) {
                                log.warn("Failed to delete file: {}", path, e);
                            }
                        });
            }
        } catch (IOException e) {
            log.error("Error deleting video files: {}", e.getMessage());
            // Continue with database deletion even if file deletion fails
        }
        
        // Delete database record (CASCADE will handle related records)
        videoRepository.delete(video);
    }
    
    @Transactional
    public VoteResponse voteOnVideo(UUID videoId, VoteRequest request, UUID userId, UUID sessionId) {
        Video video = videoRepository.findById(videoId)
                .orElseThrow(() -> new ResourceNotFoundException("Video not found: " + videoId));
        
        VoteDirection direction = VoteDirection.valueOf(request.getDirection().toUpperCase());
        
        // Check if vote already exists
        java.util.Optional<Vote> existingVote;
        if (userId != null) {
            existingVote = voteRepository.findByUserIdAndVideoId(userId, videoId);
        } else if (sessionId != null) {
            existingVote = voteRepository.findBySessionIdAndVideoId(sessionId, videoId);
        } else {
            throw new BadRequestException("Either userId or sessionId is required");
        }
        
        Vote vote;
        if (existingVote.isPresent()) {
            // Update existing vote
            vote = existingVote.get();
            vote.setDirection(direction);
        } else {
            // Create new vote
            vote = Vote.builder()
                    .userId(userId)
                    .sessionId(sessionId)
                    .videoId(videoId)
                    .direction(direction)
                    .build();
        }
        
        vote = voteRepository.save(vote);
        
        // If it's a like, add to UserLikedVideo (only for authenticated users)
        if (direction == VoteDirection.LIKE && userId != null) {
            if (!userLikedVideoRepository.existsByUserIdAndVideoId(userId, videoId)) {
                UserLikedVideo likedVideo = UserLikedVideo.builder()
                        .userId(userId)
                        .videoId(videoId)
                        .build();
                userLikedVideoRepository.save(likedVideo);
            }
        }
        
        return VoteResponse.builder()
                .message("Vote recorded")
                .videoId(videoId.toString())
                .direction(request.getDirection())
                .build();
    }
    
    @Transactional
    public ViewResponse recordView(UUID videoId, ViewRequest request, UUID userId) {
        Video video = videoRepository.findById(videoId)
                .orElseThrow(() -> new ResourceNotFoundException("Video not found: " + videoId));
        
        View view = View.builder()
                .videoId(videoId)
                .userId(userId)
                .watchedSeconds(request.getWatchedSeconds())
                .build();
        
        viewRepository.save(view);
        
        return ViewResponse.builder()
                .message("View recorded")
                .build();
    }
    
    @Transactional
    public ShareResponse shareVideo(UUID videoId, ShareRequest request) {
        Video video = videoRepository.findById(videoId)
                .orElseThrow(() -> new ResourceNotFoundException("Video not found: " + videoId));
        
        UUID sharerSessionId = UUID.fromString(request.getSharerSessionId());
        
        ShareLink shareLink = ShareLink.builder()
                .sharerSessionId(sharerSessionId)
                .videoId(videoId)
                .build();
        
        shareLink = shareLinkRepository.save(shareLink);
        
        return ShareResponse.builder()
                .message("Share link created")
                .videoId(videoId.toString())
                .shareId(shareLink.getId().toString())
                .build();
    }
    
    @Transactional
    public ShareClickResponse trackShareClick(UUID videoId, ShareClickRequest request) {
        Video video = videoRepository.findById(videoId)
                .orElseThrow(() -> new ResourceNotFoundException("Video not found: " + videoId));
        
        UUID clickerSessionId = UUID.fromString(request.getClickerSessionId());
        
        // Find the share link by sharer session ID and video ID
        List<ShareLink> shareLinks = shareLinkRepository.findByVideoId(videoId);
        ShareLink shareLink = shareLinks.stream()
                .filter(sl -> sl.getSharerSessionId().toString().equals(request.getSharerSessionId()))
                .findFirst()
                .orElse(null);
        
        if (shareLink == null) {
            // Create a new share link if not found
            shareLink = ShareLink.builder()
                    .sharerSessionId(UUID.fromString(request.getSharerSessionId()))
                    .videoId(videoId)
                    .build();
            shareLink = shareLinkRepository.save(shareLink);
        }
        
        ShareClick shareClick = ShareClick.builder()
                .shareLinkId(shareLink.getId())
                .clickerSessionId(clickerSessionId)
                .videoId(videoId)
                .build();
        
        shareClickRepository.save(shareClick);
        
        return ShareClickResponse.builder()
                .message("Share click recorded")
                .videoId(videoId.toString())
                .build();
    }
    
    @Transactional
    public void likeVideo(UUID videoId, UUID userId) {
        Video video = videoRepository.findById(videoId)
                .orElseThrow(() -> new ResourceNotFoundException("Video not found: " + videoId));
        
        if (!userLikedVideoRepository.existsByUserIdAndVideoId(userId, videoId)) {
            UserLikedVideo likedVideo = UserLikedVideo.builder()
                    .userId(userId)
                    .videoId(videoId)
                    .build();
            userLikedVideoRepository.save(likedVideo);
        }
    }
    
    @Transactional
    public void unlikeVideo(UUID videoId, UUID userId) {
        userLikedVideoRepository.findByUserIdAndVideoId(userId, videoId)
                .ifPresent(userLikedVideoRepository::delete);
    }
}

