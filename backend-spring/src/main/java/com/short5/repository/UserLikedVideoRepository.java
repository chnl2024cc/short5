package com.short5.repository;

import com.short5.entity.UserLikedVideo;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface UserLikedVideoRepository extends JpaRepository<UserLikedVideo, UUID> {
    Optional<UserLikedVideo> findByUserIdAndVideoId(UUID userId, UUID videoId);
    List<UserLikedVideo> findByUserIdOrderByCreatedAtDesc(UUID userId);
    
    @Query("SELECT ulv.videoId FROM UserLikedVideo ulv WHERE ulv.userId = :userId")
    List<UUID> findVideoIdsByUserId(@Param("userId") UUID userId);
    
    boolean existsByUserIdAndVideoId(UUID userId, UUID videoId);
}

