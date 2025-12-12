package com.short5.repository;

import com.short5.entity.ShareClick;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

@Repository
public interface ShareClickRepository extends JpaRepository<ShareClick, UUID> {
    List<ShareClick> findByVideoId(UUID videoId);
    List<ShareClick> findByShareLinkId(UUID shareLinkId);
    
    @Query("SELECT COUNT(sc) FROM ShareClick sc WHERE sc.videoId = :videoId AND sc.clickedAt >= :since")
    long countByVideoIdAndClickedAtAfter(@Param("videoId") UUID videoId, @Param("since") OffsetDateTime since);
    
    @Query("SELECT COUNT(sc) FROM ShareClick sc WHERE sc.shareLinkId = :shareLinkId")
    long countByShareLinkId(@Param("shareLinkId") UUID shareLinkId);
}

