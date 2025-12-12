package com.short5.repository;

import com.short5.entity.User;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;

import java.time.OffsetDateTime;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
class UserRepositoryTest {
    
    @Autowired
    private TestEntityManager entityManager;
    
    @Autowired
    private UserRepository userRepository;
    
    @Test
    void shouldSaveAndFindUser() {
        // Given
        User user = User.builder()
                .username("testuser")
                .email("test@example.com")
                .passwordHash("hashed_password")
                .isAdmin(false)
                .isActive(true)
                .createdAt(OffsetDateTime.now())
                .build();
        
        // When
        User saved = userRepository.save(user);
        entityManager.flush();
        entityManager.clear();
        
        Optional<User> found = userRepository.findById(saved.getId());
        
        // Then
        assertThat(found).isPresent();
        assertThat(found.get().getUsername()).isEqualTo("testuser");
        assertThat(found.get().getEmail()).isEqualTo("test@example.com");
    }
    
    @Test
    void shouldFindUserByUsername() {
        // Given
        User user = User.builder()
                .username("testuser")
                .email("test@example.com")
                .passwordHash("hashed_password")
                .isAdmin(false)
                .isActive(true)
                .createdAt(OffsetDateTime.now())
                .build();
        
        userRepository.save(user);
        entityManager.flush();
        entityManager.clear();
        
        // When
        Optional<User> found = userRepository.findByUsername("testuser");
        
        // Then
        assertThat(found).isPresent();
        assertThat(found.get().getUsername()).isEqualTo("testuser");
    }
    
    @Test
    void shouldFindUserByEmail() {
        // Given
        User user = User.builder()
                .username("testuser")
                .email("test@example.com")
                .passwordHash("hashed_password")
                .isAdmin(false)
                .isActive(true)
                .createdAt(OffsetDateTime.now())
                .build();
        
        userRepository.save(user);
        entityManager.flush();
        entityManager.clear();
        
        // When
        Optional<User> found = userRepository.findByEmail("test@example.com");
        
        // Then
        assertThat(found).isPresent();
        assertThat(found.get().getEmail()).isEqualTo("test@example.com");
    }
    
    @Test
    void shouldCheckIfUsernameExists() {
        // Given
        User user = User.builder()
                .username("testuser")
                .email("test@example.com")
                .passwordHash("hashed_password")
                .isAdmin(false)
                .isActive(true)
                .createdAt(OffsetDateTime.now())
                .build();
        
        userRepository.save(user);
        entityManager.flush();
        
        // When
        boolean exists = userRepository.existsByUsername("testuser");
        boolean notExists = userRepository.existsByUsername("nonexistent");
        
        // Then
        assertThat(exists).isTrue();
        assertThat(notExists).isFalse();
    }
    
    @Test
    void shouldCheckIfEmailExists() {
        // Given
        User user = User.builder()
                .username("testuser")
                .email("test@example.com")
                .passwordHash("hashed_password")
                .isAdmin(false)
                .isActive(true)
                .createdAt(OffsetDateTime.now())
                .build();
        
        userRepository.save(user);
        entityManager.flush();
        
        // When
        boolean exists = userRepository.existsByEmail("test@example.com");
        boolean notExists = userRepository.existsByEmail("nonexistent@example.com");
        
        // Then
        assertThat(exists).isTrue();
        assertThat(notExists).isFalse();
    }
}

