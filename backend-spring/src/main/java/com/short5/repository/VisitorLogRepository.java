package com.short5.repository;

import com.short5.entity.VisitorLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

@Repository
public interface VisitorLogRepository extends JpaRepository<VisitorLog, UUID> {
    List<VisitorLog> findBySessionId(UUID sessionId);
    List<VisitorLog> findByUserId(UUID userId);
    
    @Query("SELECT COUNT(vl) FROM VisitorLog vl WHERE vl.visitedAt >= :since")
    long countByVisitedAtAfter(@Param("since") OffsetDateTime since);
    
    @Query("SELECT COUNT(DISTINCT vl.sessionId) FROM VisitorLog vl WHERE vl.visitedAt >= :since")
    long countDistinctSessionsByVisitedAtAfter(@Param("since") OffsetDateTime since);
}

