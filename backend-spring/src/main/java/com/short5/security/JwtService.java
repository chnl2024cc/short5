package com.short5.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;

@Service
public class JwtService {
    
    @Value("${jwt.secret}")
    private String secret;
    
    @Value("${jwt.algorithm:HS256}")
    private String algorithm;
    
    @Value("${jwt.access-token-expire-minutes:30}")
    private int accessTokenExpireMinutes;
    
    @Value("${jwt.refresh-token-expire-days:7}")
    private int refreshTokenExpireDays;
    
    private SecretKey getSigningKey() {
        return Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    }
    
    public String extractUserId(String token) {
        return extractClaim(token, Claims::getSubject);
    }
    
    public String extractTokenType(String token) {
        return extractClaim(token, claims -> claims.get("type", String.class));
    }
    
    public Date extractExpiration(String token) {
        return extractClaim(token, Claims::getExpiration);
    }
    
    public <T> T extractClaim(String token, Function<Claims, T> claimsResolver) {
        final Claims claims = extractAllClaims(token);
        return claimsResolver.apply(claims);
    }
    
    private Claims extractAllClaims(String token) {
        return Jwts.parser()
                .verifyWith(getSigningKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }
    
    private Boolean isTokenExpired(String token) {
        return extractExpiration(token).before(new Date());
    }
    
    public String generateAccessToken(UUID userId) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("type", "access");
        return createToken(claims, userId.toString(), accessTokenExpireMinutes, ChronoUnit.MINUTES);
    }
    
    public String generateRefreshToken(UUID userId) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("type", "refresh");
        return createToken(claims, userId.toString(), refreshTokenExpireDays, ChronoUnit.DAYS);
    }
    
    private String createToken(Map<String, Object> claims, String subject, int amount, ChronoUnit unit) {
        Instant now = Instant.now();
        Instant expiration = now.plus(amount, unit);
        
        return Jwts.builder()
                .claims(claims)
                .subject(subject)
                .issuedAt(Date.from(now))
                .expiration(Date.from(expiration))
                .signWith(getSigningKey())
                .compact();
    }
    
    public Boolean validateToken(String token, String expectedType) {
        try {
            String tokenType = extractTokenType(token);
            return (tokenType != null && tokenType.equals(expectedType) && !isTokenExpired(token));
        } catch (Exception e) {
            return false;
        }
    }
    
    public Boolean validateAccessToken(String token) {
        return validateToken(token, "access");
    }
    
    public Boolean validateRefreshToken(String token) {
        return validateToken(token, "refresh");
    }
}

