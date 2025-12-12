# Spring Boot Development Guide

This comprehensive guide covers all aspects of developing the Spring Boot backend, including project structure, best practices, coding standards, and AI agent rules.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Best Practices & Coding Standards](#best-practices--coding-standards)
3. [AI Agent Rules](#ai-agent-rules)

---

## Project Structure

### Complete Project Directory Structure

```
backend-spring/
├── pom.xml                          # Maven build file
├── README.md                        # Project documentation
├── .gitignore                       # Git ignore rules
├── Dockerfile                       # Docker configuration
├── .cursorrules                     # AI agent rules (optional)
│
├── src/
│   ├── main/
│   │   ├── java/                   # Main source code
│   │   │   └── com/
│   │   │       └── short5/
│   │   │           ├── Short5Application.java  # Main application class
│   │   │           ├── config/                # Configuration classes
│   │   │           ├── controller/            # REST controllers
│   │   │           ├── service/               # Business logic
│   │   │           ├── repository/            # Data access layer
│   │   │           ├── entity/                # Entity classes (or model/)
│   │   │           ├── dto/                   # Data Transfer Objects
│   │   │           ├── exception/             # Custom exceptions
│   │   │           ├── security/              # Security configuration
│   │   │           └── util/                  # Utility classes
│   │   │
│   │   └── resources/              # Resources (config files, static files)
│   │       ├── application.yml    # Main configuration file
│   │       ├── application-dev.yml    # Development profile config
│   │       ├── application-prod.yml    # Production profile config
│   │       ├── application-test.yml    # Test profile config
│   │       ├── static/              # Static files (CSS, JS, images)
│   │       ├── templates/          # Template files (Thymeleaf, etc.)
│   │       └── db/
│   │           └── migration/       # Database migration scripts (if using Flyway/Liquibase)
│   │
│   └── test/
│       ├── java/                   # Test source code
│       │   └── com/
│       │       └── short5/
│       │           ├── controller/  # Controller tests
│       │           ├── service/     # Service tests
│       │           ├── repository/  # Repository tests
│       │           └── integration/  # Integration tests
│       │
│       └── resources/               # Test resources
│           ├── application-test.yml # Test configuration
│           └── test-data/           # Test data files
│
└── target/                         # Maven build output (generated, not committed)
    ├── classes/                    # Compiled classes
    ├── test-classes/               # Compiled test classes
    └── *.jar                       # Generated JAR files
```

### Directory Purpose Guide

| Directory | Purpose | What Goes Here |
|-----------|---------|----------------|
| `src/main/java/` | **Main source code** | All your Java classes (.java files) |
| `src/main/resources/` | **Configuration & resources** | YAML files, properties, static files, templates |
| `src/test/java/` | **Test source code** | All your test classes (JUnit, Mockito, etc.) |
| `src/test/resources/` | **Test resources** | Test configuration, test data files |
| `target/` or `build/` | **Build output** | Generated files (compiled classes, JARs) - **Never commit** |

### Important File Locations

**Configuration Files:**
- `src/main/resources/application.yml` - Main configuration
- `src/main/resources/application-{profile}.yml` - Profile-specific config
- `pom.xml` - Maven dependencies and build configuration

**Source Code:**
- `src/main/java/com/short5/Short5Application.java` - Main class (must be in root package)
- All other classes in sub-packages under `com.short5.*`

**Test Code:**
- `src/test/java/` - Mirror structure of `src/main/java/`
- Test classes should be in the same package as the class they test

**Static Resources:**
- `src/main/resources/static/` - Files served at `/` (CSS, JS, images)
- `src/main/resources/templates/` - Server-side templates (if using)

### Standard Package Structure

```
com.short5/
├── Short5Application.java    # Main class (in root package)
│
├── config/                   # Configuration classes (@Configuration)
│   ├── CorsConfig.java
│   ├── DatabaseConfig.java
│   ├── SecurityConfig.java
│   └── RedisConfig.java
│
├── controller/              # REST controllers (@RestController)
│   ├── UserController.java
│   ├── VideoController.java
│   └── FeedController.java
│
├── service/                 # Business logic (@Service)
│   ├── UserService.java
│   ├── VideoService.java
│   └── FeedService.java
│
├── repository/              # Data access layer (@Repository)
│   ├── UserRepository.java
│   ├── VideoRepository.java
│   └── VoteRepository.java
│
├── entity/                  # Entity classes (@Entity)
│   ├── User.java
│   ├── Video.java
│   └── Vote.java
│
├── dto/                     # Data Transfer Objects
│   ├── request/
│   │   ├── CreateUserRequest.java
│   │   └── UpdateUserRequest.java
│   └── response/
│       ├── UserResponseDto.java
│       └── VideoResponseDto.java
│
├── exception/              # Custom exceptions and handlers
│   ├── ResourceNotFoundException.java
│   ├── GlobalExceptionHandler.java
│   └── ErrorResponse.java
│
├── security/               # Security configuration and filters
│   ├── JwtTokenProvider.java
│   ├── JwtAuthenticationFilter.java
│   └── SecurityConfig.java
│
└── util/                   # Utility classes (no Spring annotations)
    ├── DateUtils.java
    └── StringUtils.java
```

### Main Application Class Location

```java
// ✅ CORRECT: Main class in root package
package com.short5;  // Root package

@SpringBootApplication
public class Short5Application {
    public static void main(String[] args) {
        SpringApplication.run(Short5Application.class, args);
    }
}

// ❌ WRONG: Main class in sub-package
package com.short5.app;  // Sub-package - Spring won't scan properly!

@SpringBootApplication
public class Short5Application {
    // This won't work correctly - Spring needs to scan from root
}
```

**Why?** Spring Boot automatically scans for components starting from the package containing `@SpringBootApplication`. If it's in a sub-package, it won't find components in parent packages.

### Common Mistakes to Avoid

- ❌ Putting Java files in root directory
- ❌ Putting application.yml in root directory
- ❌ Creating non-standard directories
- ❌ Putting main class in sub-package
- ❌ Mixing concerns (business logic in controllers)

---

## Best Practices & Coding Standards

> **✅ Verified Against Official Spring Boot Documentation**  
> This document has been cross-referenced with the official Spring Boot 3.5 documentation to ensure all practices align with current recommendations.

### Code Organization

#### ✅ DO: Use Dependency Injection

**Official Spring Boot Recommendation**: Constructor injection is the preferred method for wiring dependencies.

```java
// ✅ GOOD: Constructor injection (preferred)
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;  // final = immutable, thread-safe
    private final EmailService emailService;      // final = immutable, thread-safe
}

// ❌ BAD: Field injection makes testing harder
@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;  // Hard to test, not final
}
```

#### ✅ DO: Keep Layers Separated

- **Controllers**: Handle HTTP requests/responses, validation, and delegation to services
- **Services**: Contain business logic, orchestrate multiple repositories
- **Repositories**: Handle data access only, no business logic
- **DTOs**: Separate request/response models from entities

### Naming Conventions

- **Classes**: PascalCase (`UserService`, `UserController`)
- **Methods**: camelCase (`getUserById`, `createUser`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`)
- **Packages**: lowercase with dots (`com.short5.service`)

### Security Best Practices

#### ✅ DO: Always Validate Input

```java
@PostMapping("/users")
public ResponseEntity<UserDto> createUser(@Valid @RequestBody CreateUserRequest request) {
    return ResponseEntity.ok(userService.createUser(request));
}

public class CreateUserRequest {
    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    private String email;
    
    @NotBlank(message = "Password is required")
    @Size(min = 8, max = 100, message = "Password must be between 8 and 100 characters")
    private String password;
}
```

#### ✅ DO: Hash Passwords Properly

```java
@Service
public class PasswordService {
    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();
    
    public String encodePassword(String rawPassword) {
        return passwordEncoder.encode(rawPassword);
    }
    
    public boolean matches(String rawPassword, String encodedPassword) {
        return passwordEncoder.matches(rawPassword, encodedPassword);
    }
}
```

### Database & JPA Best Practices

#### ✅ DO: Use @Transactional Appropriately

```java
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    
    @Transactional
    public User createUserWithOrder(CreateUserRequest request) {
        User user = userRepository.save(new User(request));
        Order order = orderRepository.save(new Order(user));
        return user;
    }
    
    @Transactional(readOnly = true)
    public Optional<User> findUserById(Long id) {
        return userRepository.findById(id);
    }
}
```

#### ✅ DO: Use Optional for Nullable Returns

```java
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
}

public UserDto getUserByEmail(String email) {
    return userRepository.findByEmail(email)
        .map(this::toDto)
        .orElseThrow(() -> new UserNotFoundException("User not found: " + email));
}
```

### API Design Best Practices

#### ✅ DO: Use Proper HTTP Status Codes

```java
@PostMapping("/users")
public ResponseEntity<UserDto> createUser(@Valid @RequestBody CreateUserRequest request) {
    UserDto user = userService.createUser(request);
    return ResponseEntity.status(HttpStatus.CREATED).body(user);
}

@DeleteMapping("/users/{id}")
public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
    userService.deleteUser(id);
    return ResponseEntity.noContent().build();
}
```

#### ✅ DO: Use DTOs for Request/Response

```java
// ✅ GOOD: Separate DTOs from entities
@PostMapping("/users")
public ResponseEntity<UserResponseDto> createUser(@Valid @RequestBody CreateUserRequest request) {
    UserResponseDto user = userService.createUser(request);
    return ResponseEntity.ok(user);
}

// ❌ BAD: Exposing entities directly
@PostMapping("/users")
public ResponseEntity<User> createUser(@RequestBody User user) {
    // Exposes internal structure, can cause lazy loading issues
    return ResponseEntity.ok(userService.save(user));
}
```

### Error Handling

#### ✅ DO: Create Custom Exception Classes

```java
public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String message) {
        super(message);
    }
}

public class BadRequestException extends RuntimeException {
    public BadRequestException(String message) {
        super(message);
    }
}
```

#### ✅ DO: Use @ControllerAdvice for Global Exception Handling

```java
@ControllerAdvice
@Slf4j
public class GlobalExceptionHandler {
    
    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleResourceNotFound(ResourceNotFoundException ex) {
        log.warn("Resource not found: {}", ex.getMessage());
        ErrorResponse error = new ErrorResponse("RESOURCE_NOT_FOUND", ex.getMessage());
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
    }
    
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidationErrors(MethodArgumentNotValidException ex) {
        Map<String, String> errors = new HashMap<>();
        ex.getBindingResult().getFieldErrors().forEach(error ->
            errors.put(error.getField(), error.getDefaultMessage())
        );
        ErrorResponse error = new ErrorResponse("VALIDATION_ERROR", "Validation failed", errors);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }
}
```

### Testing Best Practices

#### ✅ DO: Write Unit Tests for Services

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    @Mock
    private UserRepository userRepository;
    
    @InjectMocks
    private UserService userService;
    
    @Test
    void shouldCreateUserSuccessfully() {
        // Given
        CreateUserRequest request = new CreateUserRequest("test@example.com", "password");
        User savedUser = new User(1L, "test@example.com");
        
        when(userRepository.existsByEmail("test@example.com")).thenReturn(false);
        when(userRepository.save(any(User.class))).thenReturn(savedUser);
        
        // When
        UserDto result = userService.createUser(request);
        
        // Then
        assertThat(result.getEmail()).isEqualTo("test@example.com");
        verify(userRepository).save(any(User.class));
    }
}
```

### NOGOs - Anti-Patterns to Avoid

1. ❌ **Don't Use @Autowired on Fields** (Use Constructor Injection)
2. ❌ **Don't Catch and Swallow Exceptions**
3. ❌ **Don't Use System.out.println for Logging** (Use SLF4J)
4. ❌ **Don't Use @Transactional on Controllers**
5. ❌ **Don't Use Eager Fetching Everywhere**
6. ❌ **Don't Return Entities from Controllers**
7. ❌ **Don't Use @Transactional on Private Methods**
8. ❌ **Don't Ignore Validation**
9. ❌ **Don't Commit Secrets or Sensitive Data**

For detailed examples and complete best practices, see the full documentation in the repository.

---

## AI Agent Rules

### Quick Reference

**Project**: Short5 Platform Backend  
**Framework**: Spring Boot 3.2.0  
**Java Version**: 17  
**Build System**: Maven  
**Package**: `com.short5`

### Core Principles

1. **Separation of Concerns**: Controllers → Services → Repositories
2. **Dependency Injection**: Always use constructor injection
3. **DTO Pattern**: Never expose entities directly in APIs
4. **Validation**: Always validate input
5. **Error Handling**: Use custom exceptions and global handlers
6. **Security First**: Hash passwords, validate input, use parameterized queries
7. **Testability**: Write testable code with proper mocking
8. **Spring Boot Conventions**: Follow framework conventions

### Mandatory Code Patterns

#### Service Class Template

```java
@Service
@RequiredArgsConstructor
@Slf4j
@Transactional
public class EntityService {
    private final EntityRepository entityRepository;
    private final OtherService otherService;
    
    @Transactional(readOnly = true)
    public EntityDto getById(Long id) {
        return entityRepository.findById(id)
            .map(this::toDto)
            .orElseThrow(() -> new ResourceNotFoundException("Entity not found: " + id));
    }
    
    @Transactional
    public EntityDto create(CreateEntityRequest request) {
        // Validation
        if (entityRepository.existsByUniqueField(request.getUniqueField())) {
            throw new BadRequestException("Entity already exists");
        }
        
        // Business logic
        Entity entity = new Entity();
        // ... set fields
        
        Entity saved = entityRepository.save(entity);
        log.info("Entity created: {}", saved.getId());
        
        return toDto(saved);
    }
    
    private EntityDto toDto(Entity entity) {
        return EntityDto.builder()
            .id(entity.getId())
            // ... map fields
            .build();
    }
}
```

#### Controller Template

```java
@RestController
@RequestMapping("/api/v1/entities")
@RequiredArgsConstructor
@Slf4j
public class EntityController {
    private final EntityService entityService;
    
    @GetMapping("/{id}")
    public ResponseEntity<EntityDto> getEntity(@PathVariable Long id) {
        return ResponseEntity.ok(entityService.getById(id));
    }
    
    @PostMapping
    public ResponseEntity<EntityDto> createEntity(
            @Valid @RequestBody CreateEntityRequest request) {
        EntityDto created = entityService.create(request);
        return ResponseEntity.status(HttpStatus.CREATED)
            .body(created);
    }
}
```

### Decision Tree: What Pattern to Use?

1. **Need to access database?** → Create Repository interface extending `JpaRepository<Entity, Long>`
2. **Need business logic?** → Create Service class with `@Service`
3. **Need HTTP endpoint?** → Create Controller with `@RestController`
4. **Need custom validation?** → Add Bean Validation annotations to DTOs
5. **Need error handling?** → Create custom exception class and add handler to `GlobalExceptionHandler`
6. **Need to cache?** → Use `@Cacheable` on service methods
7. **Need async processing?** → Use `@Async` on service methods
8. **Need events?** → Create event class extending `ApplicationEvent`

### Code Quality Checklist

Before submitting code, verify:

- [ ] Follows package structure (controller/service/repository/dto/model)
- [ ] Layers are properly separated
- [ ] Uses constructor injection with `@RequiredArgsConstructor`
- [ ] Separate DTOs for request and response
- [ ] Request DTOs have validation annotations
- [ ] Custom exceptions for domain errors
- [ ] `@Transactional` on service write methods
- [ ] Uses `Optional<>` for nullable returns
- [ ] Passwords are hashed (BCrypt)
- [ ] Input validation in place
- [ ] Unit tests for services
- [ ] Integration tests for controllers
- [ ] Proper logging with SLF4J
- [ ] No hardcoded values

---

## Additional Resources

### Official Spring Boot Documentation
- [Spring Boot Reference Documentation](https://docs.spring.io/spring-boot/docs/current/reference/html/)
- [Spring Boot Code Structure Guide](https://docs.spring.io/spring-boot/docs/current/reference/html/using.html#using.structuring-your-code)
- [Spring Data JPA Documentation](https://docs.spring.io/spring-data/jpa/docs/current/reference/html/)

### This Document
- **Verified Against**: Spring Boot 3.5 Official Documentation
- **Last Updated**: 2024
- **Version**: 1.0

