package com.short5.repository;

import com.short5.entity.View;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ViewRepository extends JpaRepository<View, UUID> {
    List<View> findByVideoId(UUID videoId);
    List<View> findByUserId(UUID userId);
    
    @Query("SELECT COUNT(v) FROM View v WHERE v.videoId = :videoId")
    long countByVideoId(@Param("videoId") UUID videoId);
    
    @Query("SELECT SUM(v.watchedSeconds) FROM View v WHERE v.videoId = :videoId")
    Long sumWatchedSecondsByVideoId(@Param("videoId") UUID videoId);
}

