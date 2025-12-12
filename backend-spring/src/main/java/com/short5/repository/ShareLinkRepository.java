package com.short5.repository;

import com.short5.entity.ShareLink;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

@Repository
public interface ShareLinkRepository extends JpaRepository<ShareLink, UUID> {
    List<ShareLink> findByVideoId(UUID videoId);
    List<ShareLink> findBySharerSessionId(UUID sharerSessionId);
    
    @Query("SELECT COUNT(sl) FROM ShareLink sl WHERE sl.videoId = :videoId AND sl.createdAt >= :since")
    long countByVideoIdAndCreatedAtAfter(@Param("videoId") UUID videoId, @Param("since") OffsetDateTime since);
}

