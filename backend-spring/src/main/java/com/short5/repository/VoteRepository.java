package com.short5.repository;

import com.short5.entity.Vote;
import com.short5.entity.Vote.VoteDirection;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface VoteRepository extends JpaRepository<Vote, UUID> {
    Optional<Vote> findByUserIdAndVideoId(UUID userId, UUID videoId);
    Optional<Vote> findBySessionIdAndVideoId(UUID sessionId, UUID videoId);
    List<Vote> findByUserId(UUID userId);
    List<Vote> findBySessionId(UUID sessionId);
    List<Vote> findByVideoId(UUID videoId);
    
    @Query("SELECT COUNT(v) FROM Vote v WHERE v.videoId = :videoId AND v.direction = :direction")
    long countByVideoIdAndDirection(@Param("videoId") UUID videoId, @Param("direction") VoteDirection direction);
    
    @Query("SELECT v.videoId FROM Vote v WHERE v.userId = :userId AND v.direction = :direction")
    List<UUID> findVideoIdsByUserIdAndDirection(@Param("userId") UUID userId, @Param("direction") VoteDirection direction);
    
    @Query("SELECT v.videoId FROM Vote v WHERE v.sessionId = :sessionId AND v.direction = :direction")
    List<UUID> findVideoIdsBySessionIdAndDirection(@Param("sessionId") UUID sessionId, @Param("direction") VoteDirection direction);
    
    @Query("SELECT v FROM Vote v WHERE v.sessionId = :sessionId")
    List<Vote> findAllBySessionId(@Param("sessionId") UUID sessionId);
}

