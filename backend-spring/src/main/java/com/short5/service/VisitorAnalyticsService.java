package com.short5.service;

import com.short5.entity.VisitorLog;
import com.short5.repository.VisitorLogRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class VisitorAnalyticsService {
    
    private final VisitorLogRepository visitorLogRepository;
    
    @Transactional(readOnly = true)
    public List<Map<String, Object>> getVisitorLocations(int days, int minVisits) {
        OffsetDateTime cutoffDate = OffsetDateTime.now().minusDays(days);
        
        List<VisitorLog> logs = visitorLogRepository.findAll().stream()
                .filter(log -> log.getVisitedAt().isAfter(cutoffDate))
                .filter(log -> log.getLatitude() != null && log.getLongitude() != null)
                .collect(Collectors.toList());
        
        // Group by location
        Map<String, List<VisitorLog>> locationGroups = logs.stream()
                .collect(Collectors.groupingBy(log -> 
                    log.getLatitude() + "," + log.getLongitude()));
        
        return locationGroups.entrySet().stream()
                .filter(entry -> entry.getValue().size() >= minVisits)
                .map(entry -> {
                    List<VisitorLog> groupLogs = entry.getValue();
                    VisitorLog first = groupLogs.get(0);
                    long uniqueVisitors = groupLogs.stream()
                            .map(VisitorLog::getSessionId)
                            .distinct()
                            .count();
                    
                    Map<String, Object> location = new HashMap<>();
                    location.put("latitude", first.getLatitude().doubleValue());
                    location.put("longitude", first.getLongitude().doubleValue());
                    location.put("country", first.getCountry());
                    location.put("country_name", first.getCountryName());
                    location.put("city", first.getCity());
                    location.put("visit_count", groupLogs.size());
                    location.put("unique_visitors", uniqueVisitors);
                    return location;
                })
                .collect(Collectors.toList());
    }
    
    @Transactional(readOnly = true)
    public Map<String, Object> getVisitorStats(int days) {
        OffsetDateTime cutoffDate = OffsetDateTime.now().minusDays(days);
        
        List<VisitorLog> logs = visitorLogRepository.findAll().stream()
                .filter(log -> log.getVisitedAt().isAfter(cutoffDate))
                .collect(Collectors.toList());
        
        long totalVisits = logs.size();
        long uniqueVisitors = logs.stream()
                .map(VisitorLog::getSessionId)
                .distinct()
                .count();
        
        long uniqueCountries = logs.stream()
                .map(VisitorLog::getCountry)
                .filter(Objects::nonNull)
                .distinct()
                .count();
        
        // Top countries
        Map<String, Long> countryCounts = logs.stream()
                .filter(log -> log.getCountry() != null)
                .collect(Collectors.groupingBy(VisitorLog::getCountry, Collectors.counting()));
        
        List<Map<String, Object>> topCountries = countryCounts.entrySet().stream()
                .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
                .limit(10)
                .map(entry -> {
                    String country = entry.getKey();
                    VisitorLog sample = logs.stream()
                            .filter(log -> country.equals(log.getCountry()))
                            .findFirst()
                            .orElse(null);
                    
                    Map<String, Object> countryData = new HashMap<>();
                    countryData.put("country", country);
                    countryData.put("country_name", sample != null ? sample.getCountryName() : null);
                    countryData.put("visits", entry.getValue());
                    countryData.put("visitors", logs.stream()
                            .filter(log -> country.equals(log.getCountry()))
                            .map(VisitorLog::getSessionId)
                            .distinct()
                            .count());
                    return countryData;
                })
                .collect(Collectors.toList());
        
        // Top cities
        Map<String, Long> cityCounts = logs.stream()
                .filter(log -> log.getCity() != null)
                .collect(Collectors.groupingBy(VisitorLog::getCity, Collectors.counting()));
        
        List<Map<String, Object>> topCities = cityCounts.entrySet().stream()
                .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
                .limit(10)
                .map(entry -> {
                    String city = entry.getKey();
                    VisitorLog sample = logs.stream()
                            .filter(log -> city.equals(log.getCity()))
                            .findFirst()
                            .orElse(null);
                    
                    Map<String, Object> cityData = new HashMap<>();
                    cityData.put("city", city);
                    cityData.put("country", sample != null ? sample.getCountry() : null);
                    cityData.put("country_name", sample != null ? sample.getCountryName() : null);
                    cityData.put("visits", entry.getValue());
                    cityData.put("visitors", logs.stream()
                            .filter(log -> city.equals(log.getCity()))
                            .map(VisitorLog::getSessionId)
                            .distinct()
                            .count());
                    return cityData;
                })
                .collect(Collectors.toList());
        
        // Top URLs
        Map<String, Long> urlCounts = logs.stream()
                .collect(Collectors.groupingBy(VisitorLog::getUrl, Collectors.counting()));
        
        List<Map<String, Object>> topUrls = urlCounts.entrySet().stream()
                .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
                .limit(20)
                .map(entry -> {
                    Map<String, Object> urlData = new HashMap<>();
                    urlData.put("url", entry.getKey());
                    urlData.put("visits", entry.getValue());
                    urlData.put("visitors", logs.stream()
                            .filter(log -> entry.getKey().equals(log.getUrl()))
                            .map(VisitorLog::getSessionId)
                            .distinct()
                            .count());
                    return urlData;
                })
                .collect(Collectors.toList());
        
        // Visits by date
        Map<String, Long> visitsByDate = logs.stream()
                .collect(Collectors.groupingBy(
                    log -> log.getVisitedAt().toLocalDate().toString(),
                    Collectors.counting()));
        
        List<Map<String, Object>> visitsByDateList = visitsByDate.entrySet().stream()
                .sorted(Map.Entry.comparingByKey())
                .map(entry -> {
                    Map<String, Object> dateData = new HashMap<>();
                    dateData.put("date", entry.getKey());
                    dateData.put("visits", entry.getValue());
                    dateData.put("visitors", logs.stream()
                            .filter(log -> entry.getKey().equals(log.getVisitedAt().toLocalDate().toString()))
                            .map(VisitorLog::getSessionId)
                            .distinct()
                            .count());
                    return dateData;
                })
                .collect(Collectors.toList());
        
        Map<String, Object> stats = new HashMap<>();
        stats.put("total_visits", totalVisits);
        stats.put("unique_visitors", uniqueVisitors);
        stats.put("unique_countries", uniqueCountries);
        stats.put("top_countries", topCountries);
        stats.put("top_cities", topCities);
        stats.put("top_urls", topUrls);
        stats.put("visits_by_date", visitsByDateList);
        
        return stats;
    }
    
    @Transactional(readOnly = true)
    public List<Map<String, Object>> getRecentVisits(int limit) {
        Pageable pageable = PageRequest.of(0, Math.min(limit, 1000));
        List<VisitorLog> visits = visitorLogRepository.findAll(pageable).getContent();
        
        return visits.stream()
                .map(visit -> {
                    Map<String, Object> visitData = new HashMap<>();
                    visitData.put("id", visit.getId().toString());
                    visitData.put("session_id", visit.getSessionId().toString());
                    visitData.put("user_id", visit.getUserId() != null ? visit.getUserId().toString() : null);
                    visitData.put("url", visit.getUrl());
                    visitData.put("country", visit.getCountry());
                    visitData.put("country_name", visit.getCountryName());
                    visitData.put("city", visit.getCity());
                    visitData.put("latitude", visit.getLatitude() != null ? visit.getLatitude().doubleValue() : null);
                    visitData.put("longitude", visit.getLongitude() != null ? visit.getLongitude().doubleValue() : null);
                    visitData.put("visited_at", visit.getVisitedAt().toString());
                    return visitData;
                })
                .collect(Collectors.toList());
    }
}

