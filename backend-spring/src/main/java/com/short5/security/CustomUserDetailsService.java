package com.short5.security;

import com.short5.entity.User;
import com.short5.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
@RequiredArgsConstructor
public class CustomUserDetailsService implements UserDetailsService {
    
    private final UserRepository userRepository;
    
    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        // In our case, username is actually the user ID (UUID)
        try {
            UUID userId = UUID.fromString(username);
            User user = userRepository.findById(userId)
                    .orElseThrow(() -> new UsernameNotFoundException("User not found: " + username));
            
            return org.springframework.security.core.userdetails.User.builder()
                    .username(user.getId().toString())
                    .password(user.getPasswordHash())
                    .authorities(user.getIsAdmin() ? "ROLE_ADMIN" : "ROLE_USER")
                    .accountExpired(!user.getIsActive())
                    .accountLocked(!user.getIsActive())
                    .credentialsExpired(false)
                    .disabled(!user.getIsActive())
                    .build();
        } catch (IllegalArgumentException e) {
            throw new UsernameNotFoundException("Invalid user ID format: " + username);
        }
    }
}

