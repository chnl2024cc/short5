package com.short5.repository;

import com.short5.entity.Video;
import com.short5.entity.Video.VideoStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface VideoRepository extends JpaRepository<Video, UUID> {
    List<Video> findByUserIdOrderByCreatedAtDesc(UUID userId);
    Page<Video> findByUserIdOrderByCreatedAtDesc(UUID userId, Pageable pageable);
    List<Video> findByStatus(VideoStatus status);
    Page<Video> findByStatusOrderByCreatedAtDesc(VideoStatus status, Pageable pageable);
    
    @Query("SELECT v FROM Video v WHERE v.status = :status ORDER BY v.createdAt DESC")
    Page<Video> findReadyVideosOrderedByCreatedAt(@Param("status") VideoStatus status, Pageable pageable);
    
    @Query("SELECT COUNT(v) FROM Video v WHERE v.userId = :userId")
    long countByUserId(@Param("userId") UUID userId);
    
    @Query("SELECT COUNT(v) FROM Video v WHERE v.userId = :userId AND v.status = :status")
    long countByUserIdAndStatus(@Param("userId") UUID userId, @Param("status") VideoStatus status);
}

