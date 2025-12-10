# Spring Boot Best Practices & Coding Rules

This document outlines the coding standards, best practices, and NOGOs (anti-patterns to avoid) for developing the Spring Boot backend application.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Code Organization](#code-organization)
3. [Naming Conventions](#naming-conventions)
4. [Security Best Practices](#security-best-practices)
5. [Database & JPA Best Practices](#database--jpa-best-practices)
6. [API Design Best Practices](#api-design-best-practices)
7. [Configuration Management](#configuration-management)
8. [Error Handling](#error-handling)
9. [Testing Best Practices](#testing-best-practices)
10. [Performance Best Practices](#performance-best-practices)
11. [Design Patterns](#design-patterns)
12. [NOGOs - Anti-Patterns to Avoid](#nogos---anti-patterns-to-avoid)

---

## Project Structure

### ✅ DO: Follow Standard Maven/Gradle Project Structure

Spring Boot follows the standard Maven/Gradle directory layout. Understanding this structure is essential for all developers.

#### Complete Project Directory Structure

```
backend-spring/
├── pom.xml                          # Maven build file (or build.gradle for Gradle)
├── README.md                        # Project documentation
├── .gitignore                       # Git ignore rules
├── Dockerfile                       # Docker configuration (if using)
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

#### Directory Purpose Guide

| Directory | Purpose | What Goes Here |
|-----------|---------|----------------|
| `src/main/java/` | **Main source code** | All your Java classes (.java files) |
| `src/main/resources/` | **Configuration & resources** | YAML files, properties, static files, templates |
| `src/test/java/` | **Test source code** | All your test classes (JUnit, Mockito, etc.) |
| `src/test/resources/` | **Test resources** | Test configuration, test data files |
| `target/` or `build/` | **Build output** | Generated files (compiled classes, JARs) - **Never commit** |

#### Important File Locations

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

#### ✅ DO: Follow Maven Standard Directory Layout

```
✅ CORRECT Structure:
src/
├── main/
│   ├── java/          ← Your Java source code
│   └── resources/      ← Configuration files
└── test/
    ├── java/          ← Your test code
    └── resources/     ← Test configuration
```

#### ❌ NOGO: Don't Create Non-Standard Directories

```java
// ❌ BAD: Putting source code in wrong location
backend-spring/
├── java/              // WRONG! Should be src/main/java/
├── config/            // WRONG! Should be src/main/resources/
└── tests/             // WRONG! Should be src/test/java/

// ❌ BAD: Putting configuration in wrong location
backend-spring/
├── application.yml    // WRONG! Should be src/main/resources/application.yml
└── config/
    └── app.yml        // WRONG! Should be src/main/resources/application.yml
```

### ✅ DO: Follow Standard Spring Boot Package Structure

Once inside `src/main/java/com/short5/`, organize your code into packages:

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
│   ├── OrderController.java
│   └── ProductController.java
│
├── service/                 # Business logic (@Service)
│   ├── UserService.java
│   ├── OrderService.java
│   └── PaymentService.java
│
├── repository/              # Data access layer (@Repository)
│   ├── UserRepository.java
│   ├── OrderRepository.java
│   └── ProductRepository.java
│
├── entity/                  # Entity classes (@Entity)
│   ├── User.java
│   ├── Order.java
│   └── Product.java
│
├── dto/                     # Data Transfer Objects
│   ├── request/
│   │   ├── CreateUserRequest.java
│   │   └── UpdateUserRequest.java
│   └── response/
│       ├── UserResponseDto.java
│       └── OrderResponseDto.java
│
├── exception/              # Custom exceptions and handlers
│   ├── UserNotFoundException.java
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

#### Package Naming Convention

- **Base package**: `com.short5` (matches your domain/company)
- **Sub-packages**: lowercase, singular nouns
- **Example**: `com.short5.service.user` (not `com.short5.services.users`)

#### Main Application Class Location

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

#### Test Structure Mirror

Your test structure should mirror your main source structure:

```
src/test/java/com/short5/
├── controller/
│   └── UserControllerTest.java
├── service/
│   └── UserServiceTest.java
└── repository/
    └── UserRepositoryTest.java
```

**Naming Convention for Tests:**
- Test class name: `{ClassName}Test.java`
- Example: `UserService.java` → `UserServiceTest.java`

### ✅ DO: Keep Layers Separated

- **Controllers**: Handle HTTP requests/responses, validation, and delegation to services
- **Services**: Contain business logic, orchestrate multiple repositories
- **Repositories**: Handle data access only, no business logic
- **DTOs**: Separate request/response models from entities

### ❌ NOGO: Don't Mix Concerns

```java
// ❌ BAD: Business logic in controller
@RestController
public class UserController {
    @GetMapping("/users/{id}")
    public User getUser(@PathVariable Long id) {
        // Business logic should not be here!
        if (user.getStatus().equals("INACTIVE")) {
            throw new RuntimeException("User is inactive");
        }
        return userRepository.findById(id);
    }
}

// ✅ GOOD: Delegate to service layer
@RestController
public class UserController {
    private final UserService userService;
    
    @GetMapping("/users/{id}")
    public ResponseEntity<UserDto> getUser(@PathVariable Long id) {
        return ResponseEntity.ok(userService.getActiveUser(id));
    }
}
```

---

## Code Organization

### ✅ DO: Use Dependency Injection

```java
// ✅ GOOD: Constructor injection (preferred)
@Service
public class UserService {
    private final UserRepository userRepository;
    private final EmailService emailService;
    
    public UserService(UserRepository userRepository, EmailService emailService) {
        this.userRepository = userRepository;
        this.emailService = emailService;
    }
}

// ✅ ACCEPTABLE: Field injection (only for optional dependencies)
@Service
public class UserService {
    @Autowired(required = false)
    private OptionalService optionalService;
}
```

### ❌ NOGO: Avoid Field Injection for Required Dependencies

```java
// ❌ BAD: Field injection makes testing harder
@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;  // Hard to test, not final
}
```

### ✅ DO: Use Lombok Appropriately

```java
// ✅ GOOD: Use @RequiredArgsConstructor for constructor injection
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    private final EmailService emailService;
}

// ✅ GOOD: Use @Data or @Getter/@Setter for DTOs
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserDto {
    private Long id;
    private String username;
    private String email;
}
```

### ❌ NOGO: Don't Overuse Lombok

```java
// ❌ BAD: Using @Data on entities can cause issues with JPA
@Entity
@Data  // Can cause problems with lazy loading, equals/hashCode
public class User {
    @Id
    @GeneratedValue
    private Long id;
    
    @OneToMany(mappedBy = "user")
    private List<Order> orders;  // Lazy loading issues!
}

// ✅ GOOD: Use specific annotations
@Entity
@Getter
@Setter
@NoArgsConstructor
@EqualsAndHashCode(onlyExplicitlyIncluded = true)
public class User {
    @Id
    @GeneratedValue
    @EqualsAndHashCode.Include
    private Long id;
    
    @OneToMany(mappedBy = "user")
    private List<Order> orders;
}
```

---

## Naming Conventions

### ✅ DO: Follow Java Naming Conventions

- **Classes**: PascalCase (`UserService`, `UserController`)
- **Methods**: camelCase (`getUserById`, `createUser`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`)
- **Packages**: lowercase with dots (`com.short5.service`)

### ✅ DO: Use Descriptive Names

```java
// ✅ GOOD: Clear and descriptive
public User findActiveUserById(Long userId) { }
public List<Order> getPendingOrdersForUser(Long userId) { }

// ❌ BAD: Unclear abbreviations
public User findUsr(Long id) { }
public List<Order> getPO(Long uid) { }
```

### ✅ DO: Use Repository Method Naming Conventions

```java
// ✅ GOOD: Spring Data JPA query methods
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
    List<User> findByStatusAndCreatedAtAfter(String status, LocalDateTime date);
    boolean existsByEmail(String email);
    long countByStatus(String status);
}
```

---

## Security Best Practices

### ✅ DO: Always Validate Input

```java
// ✅ GOOD: Use Bean Validation
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

### ✅ DO: Use Parameterized Queries (JPA handles this automatically)

```java
// ✅ GOOD: JPA Repository (automatically parameterized)
public interface UserRepository extends JpaRepository<User, Long> {
    @Query("SELECT u FROM User u WHERE u.email = :email")
    Optional<User> findByEmail(@Param("email") String email);
}

// ❌ NOGO: Never use string concatenation for queries
// This is handled automatically by JPA, but if using JDBC:
// ❌ BAD: String sql = "SELECT * FROM users WHERE email = '" + email + "'";
```

### ✅ DO: Hash Passwords Properly

```java
// ✅ GOOD: Use BCryptPasswordEncoder
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

### ❌ NOGO: Never Store Plain Text Passwords

```java
// ❌ BAD: Never do this!
user.setPassword(request.getPassword());  // Plain text!
```

### ✅ DO: Use HTTPS in Production

- Always configure SSL/TLS in production
- Use environment variables for sensitive configuration

### ✅ DO: Implement Proper CORS Configuration

```java
// ✅ GOOD: Specific origins, not wildcard
@Configuration
public class CorsConfig {
    @Value("${cors.allowed-origins}")
    private List<String> allowedOrigins;
    
    @Bean
    public CorsFilter corsFilter() {
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowedOrigins(allowedOrigins);  // Specific origins
        config.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE"));
        config.setAllowCredentials(true);
        // ... rest of config
    }
}
```

### ❌ NOGO: Don't Use Wildcard CORS in Production

```java
// ❌ BAD: Security risk
config.setAllowedOrigins(Arrays.asList("*"));  // Too permissive!
```

---

## Database & JPA Best Practices

### ✅ DO: Use @Transactional Appropriately

```java
// ✅ GOOD: Service methods that modify data should be transactional
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    private final OrderRepository orderRepository;
    
    @Transactional
    public User createUserWithOrder(CreateUserRequest request) {
        User user = userRepository.save(new User(request));
        Order order = orderRepository.save(new Order(user));
        return user;
    }
    
    // Read-only operations can use @Transactional(readOnly = true)
    @Transactional(readOnly = true)
    public Optional<User> findUserById(Long id) {
        return userRepository.findById(id);
    }
}
```

### ❌ NOGO: Don't Use @Transactional on Controllers

```java
// ❌ BAD: Transactions belong in service layer
@RestController
@Transactional  // NO! Transactions in controller
public class UserController { }
```

### ✅ DO: Use Lazy Loading for Relationships

```java
// ✅ GOOD: Lazy loading by default
@Entity
public class User {
    @OneToMany(mappedBy = "user", fetch = FetchType.LAZY)
    private List<Order> orders;
}

// ✅ GOOD: Eager loading only when necessary and with caution
@Entity
public class Order {
    @ManyToOne(fetch = FetchType.EAGER)  // Only if always needed
    private User user;
}
```

### ❌ NOGO: Avoid N+1 Query Problems

```java
// ❌ BAD: Causes N+1 queries
@Transactional(readOnly = true)
public List<User> getAllUsers() {
    List<User> users = userRepository.findAll();
    // This will cause N+1 queries if orders are accessed
    users.forEach(user -> user.getOrders().size());
    return users;
}

// ✅ GOOD: Use JOIN FETCH
@Query("SELECT DISTINCT u FROM User u LEFT JOIN FETCH u.orders")
List<User> findAllWithOrders();

// ✅ GOOD: Use @EntityGraph
@EntityGraph(attributePaths = {"orders"})
List<User> findAll();
```

### ✅ DO: Use Optional for Nullable Returns

```java
// ✅ GOOD: Use Optional
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
}

// ✅ GOOD: Handle Optional properly
public UserDto getUserByEmail(String email) {
    return userRepository.findByEmail(email)
        .map(this::toDto)
        .orElseThrow(() -> new UserNotFoundException("User not found: " + email));
}
```

### ❌ NOGO: Don't Return Null from Repository Methods

```java
// ❌ BAD: Returning null
public User findByEmail(String email) {
    // Returns null if not found - use Optional instead
}

// ❌ BAD: Not handling null
User user = userRepository.findByEmail(email);
user.getName();  // NullPointerException if user is null!
```

### ✅ DO: Use @CreatedDate and @LastModifiedDate

```java
// ✅ GOOD: Automatic timestamp management
@Entity
@EntityListeners(AuditingEntityListener.class)
public class User {
    @Id
    @GeneratedValue
    private Long id;
    
    @CreatedDate
    private LocalDateTime createdAt;
    
    @LastModifiedDate
    private LocalDateTime updatedAt;
}
```

### ✅ DO: Use Soft Deletes When Appropriate

```java
// ✅ GOOD: Soft delete pattern
@Entity
public class User {
    @Id
    @GeneratedValue
    private Long id;
    
    @Column(nullable = false)
    private boolean deleted = false;
    
    private LocalDateTime deletedAt;
}

// Repository
@Query("SELECT u FROM User u WHERE u.deleted = false")
List<User> findAllActive();
```

---

## API Design Best Practices

### ✅ DO: Use Proper HTTP Status Codes

```java
// ✅ GOOD: Appropriate status codes
@PostMapping("/users")
public ResponseEntity<UserDto> createUser(@Valid @RequestBody CreateUserRequest request) {
    UserDto user = userService.createUser(request);
    return ResponseEntity.status(HttpStatus.CREATED).body(user);
}

@GetMapping("/users/{id}")
public ResponseEntity<UserDto> getUser(@PathVariable Long id) {
    return ResponseEntity.ok(userService.getUserById(id));
}

@DeleteMapping("/users/{id}")
public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
    userService.deleteUser(id);
    return ResponseEntity.noContent().build();
}
```

### ✅ DO: Use DTOs for Request/Response

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

### ✅ DO: Use Consistent API Versioning

```java
// ✅ GOOD: API versioning
@RestController
@RequestMapping("/api/v1/users")
public class UserController { }

// Or use headers for versioning
@RequestMapping(value = "/api/users", headers = "API-Version=1")
```

### ✅ DO: Implement Pagination

```java
// ✅ GOOD: Pagination support
@GetMapping("/users")
public ResponseEntity<Page<UserDto>> getUsers(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size,
        @RequestParam(defaultValue = "id") String sortBy) {
    Pageable pageable = PageRequest.of(page, size, Sort.by(sortBy));
    return ResponseEntity.ok(userService.getAllUsers(pageable));
}
```

### ❌ NOGO: Don't Return Large Lists Without Pagination

```java
// ❌ BAD: Can cause performance issues
@GetMapping("/users")
public List<User> getAllUsers() {
    return userRepository.findAll();  // Could be thousands of records!
}
```

---

## Configuration Management

### ✅ DO: Use application.yml for Configuration

```yaml
# ✅ GOOD: Environment-specific configuration
spring:
  profiles:
    active: ${SPRING_PROFILES_ACTIVE:dev}
  
  datasource:
    url: ${DATABASE_URL:jdbc:postgresql://localhost:5432/short5}
    username: ${DATABASE_USERNAME:postgres}
    password: ${DATABASE_PASSWORD:postgres}

cors:
  allowed-origins: ${CORS_ALLOWED_ORIGINS:http://localhost:3000}
```

### ✅ DO: Use @ConfigurationProperties for Complex Configuration

```java
// ✅ GOOD: Type-safe configuration
@ConfigurationProperties(prefix = "app.file-storage")
@Data
public class FileStorageProperties {
    private String uploadDir;
    private long maxFileSize;
    private List<String> allowedExtensions;
}
```

### ❌ NOGO: Don't Hardcode Configuration Values

```java
// ❌ BAD: Hardcoded values
private static final String UPLOAD_DIR = "/var/uploads";
private static final int MAX_SIZE = 10485760;

// ✅ GOOD: Use configuration
@Value("${app.file-storage.upload-dir}")
private String uploadDir;
```

### ✅ DO: Use Environment Variables for Secrets

- Never commit secrets to version control
- Use environment variables or secret management tools
- Use `.env` files for local development (add to `.gitignore`)

---

## Error Handling

### ✅ DO: Create Custom Exception Classes

```java
// ✅ GOOD: Custom exceptions
public class UserNotFoundException extends RuntimeException {
    public UserNotFoundException(String message) {
        super(message);
    }
}

public class EmailAlreadyExistsException extends RuntimeException {
    public EmailAlreadyExistsException(String email) {
        super("Email already exists: " + email);
    }
}
```

### ✅ DO: Use @ControllerAdvice for Global Exception Handling

```java
// ✅ GOOD: Centralized exception handling
@ControllerAdvice
@Slf4j
public class GlobalExceptionHandler {
    
    @ExceptionHandler(UserNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleUserNotFound(UserNotFoundException ex) {
        log.error("User not found", ex);
        ErrorResponse error = new ErrorResponse("USER_NOT_FOUND", ex.getMessage());
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
    
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGenericException(Exception ex) {
        log.error("Unexpected error", ex);
        ErrorResponse error = new ErrorResponse("INTERNAL_ERROR", "An unexpected error occurred");
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }
}
```

### ❌ NOGO: Don't Expose Internal Errors to Clients

```java
// ❌ BAD: Exposing stack traces
@ExceptionHandler(Exception.class)
public ResponseEntity<String> handleException(Exception ex) {
    return ResponseEntity.status(500).body(ex.getMessage() + "\n" + 
        Arrays.toString(ex.getStackTrace()));  // Security risk!
}
```

---

## Testing Best Practices

### ✅ DO: Write Unit Tests for Services

```java
// ✅ GOOD: Unit test with mocks
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    
    @Mock
    private UserRepository userRepository;
    
    @Mock
    private EmailService emailService;
    
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

### ✅ DO: Write Integration Tests for Controllers

```java
// ✅ GOOD: Integration test
@SpringBootTest
@AutoConfigureMockMvc
class UserControllerIntegrationTest {
    
    @Autowired
    private MockMvc mockMvc;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    @Test
    void shouldCreateUser() throws Exception {
        CreateUserRequest request = new CreateUserRequest("test@example.com", "password123");
        
        mockMvc.perform(post("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.email").value("test@example.com"));
    }
}
```

### ✅ DO: Use @DataJpaTest for Repository Tests

```java
// ✅ GOOD: Repository test
@DataJpaTest
class UserRepositoryTest {
    
    @Autowired
    private TestEntityManager entityManager;
    
    @Autowired
    private UserRepository userRepository;
    
    @Test
    void shouldFindUserByEmail() {
        // Given
        User user = new User("test@example.com", "password");
        entityManager.persistAndFlush(user);
        
        // When
        Optional<User> found = userRepository.findByEmail("test@example.com");
        
        // Then
        assertThat(found).isPresent();
        assertThat(found.get().getEmail()).isEqualTo("test@example.com");
    }
}
```

### ❌ NOGO: Don't Skip Testing

- Always write tests for business logic
- Aim for at least 70% code coverage
- Test edge cases and error scenarios

---

## Performance Best Practices

### ✅ DO: Use @Cacheable for Expensive Operations

```java
// ✅ GOOD: Caching expensive operations
@Service
public class UserService {
    
    @Cacheable(value = "users", key = "#id")
    public UserDto getUserById(Long id) {
        // Expensive database query
        return userRepository.findById(id)
            .map(this::toDto)
            .orElseThrow(() -> new UserNotFoundException("User not found"));
    }
    
    @CacheEvict(value = "users", key = "#id")
    public void updateUser(Long id, UpdateUserRequest request) {
        // Update logic
    }
}
```

### ✅ DO: Use @Async for Long-Running Tasks

```java
// ✅ GOOD: Async processing
@Service
public class EmailService {
    
    @Async
    public CompletableFuture<Void> sendWelcomeEmail(String email) {
        // Long-running email sending
        return CompletableFuture.completedFuture(null);
    }
}

// Enable async in configuration
@Configuration
@EnableAsync
public class AsyncConfig { }
```

### ✅ DO: Use Connection Pooling

```yaml
# ✅ GOOD: Configure connection pool
spring:
  datasource:
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
      connection-timeout: 30000
```

### ❌ NOGO: Don't Load Entire Collections Unnecessarily

```java
// ❌ BAD: Loading all users into memory
List<User> users = userRepository.findAll();
users.stream().filter(u -> u.isActive()).collect(Collectors.toList());

// ✅ GOOD: Filter at database level
@Query("SELECT u FROM User u WHERE u.active = true")
List<User> findActiveUsers();
```

---

## Design Patterns

Design patterns are proven solutions to common problems in software design. This section outlines the design patterns we should use when developing Spring Boot applications.

### 1. Dependency Injection (DI) Pattern

**When to Use**: Always - This is the foundation of Spring Framework

**Description**: Objects receive their dependencies from external sources rather than creating them internally.

```java
// ✅ GOOD: Constructor injection (preferred pattern)
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    private final EmailService emailService;
    private final NotificationService notificationService;
    
    public UserDto createUser(CreateUserRequest request) {
        User user = userRepository.save(new User(request));
        emailService.sendWelcomeEmail(user.getEmail());
        notificationService.notifyUserCreated(user);
        return toDto(user);
    }
}
```

**Benefits**:
- Loose coupling
- Easy testing (can inject mocks)
- Single Responsibility Principle
- Inversion of Control

---

### 2. Repository Pattern

**When to Use**: Always for data access layer

**Description**: Abstracts data access logic and provides a collection-like interface for accessing domain objects.

```java
// ✅ GOOD: Repository pattern with Spring Data JPA
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
    List<User> findByStatusAndCreatedAtAfter(String status, LocalDateTime date);
    boolean existsByEmail(String email);
    
    // Custom query when needed
    @Query("SELECT u FROM User u WHERE u.email = :email AND u.active = true")
    Optional<User> findActiveUserByEmail(@Param("email") String email);
}
```

**Benefits**:
- Separation of data access from business logic
- Easy to test (can mock repositories)
- Consistent data access interface
- Spring Data JPA provides implementation automatically

---

### 3. Service Layer Pattern

**When to Use**: Always for business logic

**Description**: Encapsulates business logic and orchestrates operations between repositories and other services.

```java
// ✅ GOOD: Service layer with clear responsibilities
@Service
@RequiredArgsConstructor
@Transactional
public class UserService {
    private final UserRepository userRepository;
    private final PasswordService passwordService;
    private final EmailService emailService;
    private final AuditService auditService;
    
    public UserDto createUser(CreateUserRequest request) {
        // Business logic validation
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new EmailAlreadyExistsException(request.getEmail());
        }
        
        // Business logic execution
        User user = new User();
        user.setEmail(request.getEmail());
        user.setPassword(passwordService.encode(request.getPassword()));
        user.setStatus(UserStatus.ACTIVE);
        
        User savedUser = userRepository.save(user);
        
        // Side effects
        emailService.sendWelcomeEmail(savedUser.getEmail());
        auditService.logUserCreated(savedUser.getId());
        
        return toDto(savedUser);
    }
}
```

**Benefits**:
- Centralized business logic
- Reusable across different controllers
- Easy to test
- Transaction management

---

### 4. DTO (Data Transfer Object) Pattern

**When to Use**: Always when exposing data through APIs

**Description**: Objects that carry data between processes/network boundaries without exposing internal structure.

```java
// ✅ GOOD: Separate DTOs for request and response
// Request DTO
@Data
@NoArgsConstructor
@AllArgsConstructor
public class CreateUserRequest {
    @NotBlank
    @Email
    private String email;
    
    @NotBlank
    @Size(min = 8)
    private String password;
}

// Response DTO
@Data
@Builder
public class UserResponseDto {
    private Long id;
    private String email;
    private String username;
    private UserStatus status;
    private LocalDateTime createdAt;
}

// Service with mapping
@Service
public class UserService {
    public UserResponseDto createUser(CreateUserRequest request) {
        User user = // ... create user
        return toDto(user);
    }
    
    private UserResponseDto toDto(User user) {
        return UserResponseDto.builder()
            .id(user.getId())
            .email(user.getEmail())
            .username(user.getUsername())
            .status(user.getStatus())
            .createdAt(user.getCreatedAt())
            .build();
    }
}
```

**Benefits**:
- Decouples internal model from API contract
- Prevents lazy loading issues
- Allows versioning of API
- Security (hides sensitive fields)

---

### 5. Builder Pattern

**When to Use**: For complex object construction, especially DTOs and configuration

**Description**: Constructs complex objects step by step.

```java
// ✅ GOOD: Using Lombok @Builder
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserDto {
    private Long id;
    private String email;
    private String username;
    private List<String> roles;
    private UserProfile profile;
}

// Usage
UserDto user = UserDto.builder()
    .id(1L)
    .email("user@example.com")
    .username("john_doe")
    .roles(Arrays.asList("USER", "ADMIN"))
    .profile(UserProfile.builder()
        .firstName("John")
        .lastName("Doe")
        .build())
    .build();
```

**Benefits**:
- Clear, readable object construction
- Handles optional parameters well
- Immutable objects when combined with final fields

---

### 6. Strategy Pattern

**When to Use**: When you have multiple algorithms/behaviors that can be interchanged

**Description**: Defines a family of algorithms, encapsulates each one, and makes them interchangeable.

```java
// ✅ GOOD: Strategy pattern for payment processing
public interface PaymentStrategy {
    PaymentResult processPayment(PaymentRequest request);
}

@Component("creditCard")
public class CreditCardPaymentStrategy implements PaymentStrategy {
    @Override
    public PaymentResult processPayment(PaymentRequest request) {
        // Credit card processing logic
        return new PaymentResult(true, "Payment processed via credit card");
    }
}

@Component("paypal")
public class PayPalPaymentStrategy implements PaymentStrategy {
    @Override
    public PaymentResult processPayment(PaymentRequest request) {
        // PayPal processing logic
        return new PaymentResult(true, "Payment processed via PayPal");
    }
}

// Service using strategy
@Service
@RequiredArgsConstructor
public class PaymentService {
    private final Map<String, PaymentStrategy> strategies;
    
    public PaymentService(List<PaymentStrategy> strategyList) {
        this.strategies = strategyList.stream()
            .collect(Collectors.toMap(
                s -> s.getClass().getAnnotation(Component.class).value(),
                Function.identity()
            ));
    }
    
    public PaymentResult processPayment(String paymentType, PaymentRequest request) {
        PaymentStrategy strategy = strategies.get(paymentType);
        if (strategy == null) {
            throw new UnsupportedPaymentTypeException(paymentType);
        }
        return strategy.processPayment(request);
    }
}
```

**Benefits**:
- Easy to add new strategies
- Open/Closed Principle
- Removes conditional logic
- Easy to test each strategy independently

---

### 7. Factory Pattern

**When to Use**: When object creation logic is complex or needs to be centralized

**Description**: Creates objects without exposing the instantiation logic.

```java
// ✅ GOOD: Factory for creating different notification types
public interface Notification {
    void send(String recipient, String message);
}

@Component
public class NotificationFactory {
    private final Map<String, Notification> notifications;
    
    public NotificationFactory(List<Notification> notificationList) {
        this.notifications = notificationList.stream()
            .collect(Collectors.toMap(
                n -> n.getClass().getSimpleName().replace("Notification", "").toLowerCase(),
                Function.identity()
            ));
    }
    
    public Notification getNotification(String type) {
        Notification notification = notifications.get(type.toLowerCase());
        if (notification == null) {
            throw new UnsupportedNotificationTypeException(type);
        }
        return notification;
    }
}

// Usage
@Service
@RequiredArgsConstructor
public class NotificationService {
    private final NotificationFactory factory;
    
    public void sendNotification(String type, String recipient, String message) {
        Notification notification = factory.getNotification(type);
        notification.send(recipient, message);
    }
}
```

**Benefits**:
- Centralized object creation
- Easy to extend with new types
- Hides complex creation logic

---

### 8. Observer Pattern (Event-Driven)

**When to Use**: When you need to notify multiple components about events

**Description**: Objects notify observers about state changes. Spring's ApplicationEventPublisher implements this.

```java
// ✅ GOOD: Using Spring Events
// Event class
public class UserCreatedEvent extends ApplicationEvent {
    private final Long userId;
    private final String email;
    
    public UserCreatedEvent(Object source, Long userId, String email) {
        super(source);
        this.userId = userId;
        this.email = email;
    }
    
    public Long getUserId() { return userId; }
    public String getEmail() { return email; }
}

// Publisher
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    private final ApplicationEventPublisher eventPublisher;
    
    @Transactional
    public UserDto createUser(CreateUserRequest request) {
        User user = userRepository.save(new User(request));
        
        // Publish event
        eventPublisher.publishEvent(new UserCreatedEvent(this, user.getId(), user.getEmail()));
        
        return toDto(user);
    }
}

// Listeners
@Component
@Slf4j
public class UserEventListener {
    
    @EventListener
    @Async
    public void handleUserCreated(UserCreatedEvent event) {
        log.info("User created: {}", event.getUserId());
        // Send welcome email, create audit log, etc.
    }
    
    @EventListener
    @Async
    public void sendWelcomeEmail(UserCreatedEvent event) {
        emailService.sendWelcomeEmail(event.getEmail());
    }
}
```

**Benefits**:
- Loose coupling between components
- Easy to add new listeners
- Asynchronous processing support
- Follows Single Responsibility Principle

---

### 9. Template Method Pattern

**When to Use**: When you have common algorithm structure with varying steps

**Description**: Defines the skeleton of an algorithm, letting subclasses override specific steps.

```java
// ✅ GOOD: Template method for data export
public abstract class DataExporter {
    
    // Template method
    public final void export(List<Data> data, String filename) {
        validateData(data);
        String formattedData = formatData(data);
        byte[] processedData = processData(formattedData);
        saveToFile(processedData, filename);
        notifyCompletion(filename);
    }
    
    protected void validateData(List<Data> data) {
        if (data == null || data.isEmpty()) {
            throw new IllegalArgumentException("Data cannot be empty");
        }
    }
    
    protected abstract String formatData(List<Data> data);
    
    protected byte[] processData(String data) {
        return data.getBytes();
    }
    
    protected abstract void saveToFile(byte[] data, String filename);
    
    protected void notifyCompletion(String filename) {
        log.info("Export completed: {}", filename);
    }
}

// Concrete implementations
@Component
public class CsvExporter extends DataExporter {
    @Override
    protected String formatData(List<Data> data) {
        // CSV formatting logic
        return csvFormatter.format(data);
    }
    
    @Override
    protected void saveToFile(byte[] data, String filename) {
        fileService.save(data, filename + ".csv");
    }
}

@Component
public class JsonExporter extends DataExporter {
    @Override
    protected String formatData(List<Data> data) {
        // JSON formatting logic
        return objectMapper.writeValueAsString(data);
    }
    
    @Override
    protected void saveToFile(byte[] data, String filename) {
        fileService.save(data, filename + ".json");
    }
}
```

**Benefits**:
- Code reuse
- Consistent algorithm structure
- Easy to add new implementations

---

### 10. Facade Pattern

**When to Use**: When you need to simplify complex subsystem interactions

**Description**: Provides a simplified interface to a complex subsystem.

```java
// ✅ GOOD: Facade for complex order processing
@Service
@RequiredArgsConstructor
public class OrderFacade {
    private final OrderService orderService;
    private final InventoryService inventoryService;
    private final PaymentService paymentService;
    private final ShippingService shippingService;
    private final NotificationService notificationService;
    
    @Transactional
    public OrderDto processOrder(CreateOrderRequest request) {
        // Complex orchestration hidden behind simple interface
        Order order = orderService.createOrder(request);
        inventoryService.reserveItems(order.getItems());
        PaymentResult payment = paymentService.processPayment(order.getPaymentInfo());
        
        if (!payment.isSuccess()) {
            inventoryService.releaseItems(order.getItems());
            throw new PaymentFailedException("Payment processing failed");
        }
        
        shippingService.scheduleShipment(order);
        notificationService.sendOrderConfirmation(order);
        
        return toDto(order);
    }
}
```

**Benefits**:
- Simplifies complex operations
- Reduces coupling
- Provides a clean API

---

### 11. Singleton Pattern (Spring Managed)

**When to Use**: When you need exactly one instance (Spring handles this automatically)

**Description**: Ensures a class has only one instance. Spring's default bean scope is singleton.

```java
// ✅ GOOD: Spring automatically manages singleton scope
@Service  // Default scope is singleton
public class ConfigurationService {
    private final Map<String, String> cache = new ConcurrentHashMap<>();
    
    public String getConfig(String key) {
        return cache.computeIfAbsent(key, this::loadFromDatabase);
    }
}

// If you need different scopes:
@Service
@Scope(ConfigurableBeanFactory.SCOPE_PROTOTYPE)  // New instance each time
public class PrototypeService { }

@Service
@Scope(WebApplicationContext.SCOPE_REQUEST)  // One per HTTP request
public class RequestScopedService { }
```

**Benefits**:
- Controlled access to single instance
- Lazy initialization
- Thread-safe (when properly implemented)
- Spring manages lifecycle automatically

---

### 12. Adapter Pattern

**When to Use**: When integrating with external systems or legacy code

**Description**: Allows incompatible interfaces to work together.

```java
// ✅ GOOD: Adapter for external payment gateway
public interface PaymentGateway {
    PaymentResult charge(CreditCard card, BigDecimal amount);
}

// External library interface (incompatible)
public class LegacyPaymentProcessor {
    public boolean processPayment(String cardNumber, double amount) {
        // Legacy implementation
    }
}

// Adapter
@Component
public class LegacyPaymentAdapter implements PaymentGateway {
    private final LegacyPaymentProcessor legacyProcessor;
    
    @Override
    public PaymentResult charge(CreditCard card, BigDecimal amount) {
        boolean success = legacyProcessor.processPayment(
            card.getNumber(), 
            amount.doubleValue()
        );
        return new PaymentResult(success, success ? "Success" : "Failed");
    }
}

// Service uses adapter transparently
@Service
@RequiredArgsConstructor
public class PaymentService {
    private final PaymentGateway paymentGateway;  // Uses adapter
    
    public void processPayment(PaymentRequest request) {
        paymentGateway.charge(request.getCard(), request.getAmount());
    }
}
```

**Benefits**:
- Integrates incompatible interfaces
- Wraps legacy code
- Maintains clean service layer

---

### 13. Decorator Pattern

**When to Use**: When you need to add behavior to objects dynamically

**Description**: Attaches additional responsibilities to objects dynamically.

```java
// ✅ GOOD: Decorator for adding caching to service
public interface UserService {
    UserDto getUserById(Long id);
}

@Service
@Primary
public class CachingUserServiceDecorator implements UserService {
    private final UserService delegate;
    private final CacheManager cacheManager;
    
    public CachingUserServiceDecorator(UserServiceImpl delegate, CacheManager cacheManager) {
        this.delegate = delegate;
        this.cacheManager = cacheManager;
    }
    
    @Override
    public UserDto getUserById(Long id) {
        String cacheKey = "user:" + id;
        UserDto cached = cacheManager.get(cacheKey, UserDto.class);
        if (cached != null) {
            return cached;
        }
        
        UserDto user = delegate.getUserById(id);
        cacheManager.put(cacheKey, user);
        return user;
    }
}
```

**Benefits**:
- Add behavior without modifying original class
- Compose behaviors dynamically
- Follows Open/Closed Principle

---

### 14. Chain of Responsibility Pattern

**When to Use**: When you need to process requests through a chain of handlers

**Description**: Passes requests along a chain of handlers.

```java
// ✅ GOOD: Request processing chain
public interface RequestHandler {
    void handle(Request request);
    void setNext(RequestHandler handler);
}

@Component
public class AuthenticationHandler implements RequestHandler {
    private RequestHandler next;
    
    @Override
    public void handle(Request request) {
        if (!isAuthenticated(request)) {
            throw new AuthenticationException("Not authenticated");
        }
        if (next != null) {
            next.handle(request);
        }
    }
    
    @Override
    public void setNext(RequestHandler handler) {
        this.next = handler;
    }
}

@Component
public class AuthorizationHandler implements RequestHandler {
    private RequestHandler next;
    
    @Override
    public void handle(Request request) {
        if (!hasPermission(request)) {
            throw new AuthorizationException("Not authorized");
        }
        if (next != null) {
            next.handle(request);
        }
    }
    
    @Override
    public void setNext(RequestHandler handler) {
        this.next = handler;
    }
}

// Configure chain
@Configuration
public class RequestHandlerChain {
    @Bean
    public RequestHandler requestHandlerChain(
            AuthenticationHandler authHandler,
            AuthorizationHandler authzHandler) {
        authHandler.setNext(authzHandler);
        return authHandler;
    }
}
```

**Benefits**:
- Decouples sender and receiver
- Dynamic chain composition
- Easy to add/remove handlers

---

### Pattern Selection Guidelines

**Use Dependency Injection**: Always - Foundation of Spring

**Use Repository Pattern**: Always - For all data access

**Use Service Layer**: Always - For all business logic

**Use DTO Pattern**: Always - For all API boundaries

**Use Builder Pattern**: When constructing complex objects

**Use Strategy Pattern**: When you have multiple interchangeable algorithms

**Use Factory Pattern**: When object creation is complex

**Use Observer Pattern**: When multiple components need to react to events

**Use Template Method**: When you have common algorithm structure

**Use Facade Pattern**: When simplifying complex subsystem interactions

**Use Adapter Pattern**: When integrating incompatible interfaces

**Use Decorator Pattern**: When adding behavior dynamically

**Use Chain of Responsibility**: When processing through multiple handlers

---

### ❌ NOGO: Anti-Patterns in Design Patterns

```java
// ❌ BAD: God Object - Service doing too much
@Service
public class UserService {
    // Handles users, orders, payments, notifications, etc.
    // Too many responsibilities!
}

// ✅ GOOD: Split into focused services
@Service
public class UserService { /* User-specific logic */ }
@Service
public class OrderService { /* Order-specific logic */ }
@Service
public class PaymentService { /* Payment-specific logic */ }
```

```java
// ❌ BAD: Anemic Domain Model - Entities with no behavior
@Entity
public class User {
    private Long id;
    private String email;
    // Only getters/setters, no business logic
}

// ✅ GOOD: Rich Domain Model
@Entity
public class User {
    private Long id;
    private String email;
    private UserStatus status;
    
    public void activate() {
        if (this.status == UserStatus.BANNED) {
            throw new IllegalStateException("Cannot activate banned user");
        }
        this.status = UserStatus.ACTIVE;
    }
    
    public boolean canPlaceOrder() {
        return status == UserStatus.ACTIVE && !isSuspended();
    }
}
```

---

## NOGOs - Anti-Patterns to Avoid

### ❌ NOGO: Don't Use @Autowired on Fields (Use Constructor Injection)

```java
// ❌ BAD
@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;
}

// ✅ GOOD
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
}
```

### ❌ NOGO: Don't Catch and Swallow Exceptions

```java
// ❌ BAD: Swallowing exceptions
try {
    userService.deleteUser(id);
} catch (Exception e) {
    // Silent failure - very bad!
}

// ✅ GOOD: Log and handle appropriately
try {
    userService.deleteUser(id);
} catch (UserNotFoundException e) {
    log.warn("User not found: {}", id);
    throw e;  // Re-throw or handle appropriately
}
```

### ❌ NOGO: Don't Use System.out.println for Logging

```java
// ❌ BAD: Use proper logging
System.out.println("User created: " + user.getId());

// ✅ GOOD: Use SLF4J
@Slf4j
public class UserService {
    public void createUser(User user) {
        log.info("User created: {}", user.getId());
    }
}
```

### ❌ NOGO: Don't Ignore @Transactional Propagation

```java
// ❌ BAD: Not understanding transaction propagation
@Transactional
public void method1() {
    method2();  // Runs in same transaction
}

@Transactional(propagation = Propagation.REQUIRES_NEW)
public void method2() {
    // This creates a new transaction - understand the implications!
}
```

### ❌ NOGO: Don't Use Eager Fetching Everywhere

```java
// ❌ BAD: Eager fetching can cause performance issues
@Entity
public class User {
    @OneToMany(fetch = FetchType.EAGER)  // Loads all orders always
    private List<Order> orders;
}

// ✅ GOOD: Use lazy loading and fetch when needed
@Entity
public class User {
    @OneToMany(fetch = FetchType.LAZY)
    private List<Order> orders;
}
```

### ❌ NOGO: Don't Return Entities from Controllers

```java
// ❌ BAD: Exposes internal structure
@GetMapping("/users/{id}")
public User getUser(@PathVariable Long id) {
    return userRepository.findById(id).orElse(null);
}

// ✅ GOOD: Return DTOs
@GetMapping("/users/{id}")
public ResponseEntity<UserDto> getUser(@PathVariable Long id) {
    return ResponseEntity.ok(userService.getUserById(id));
}
```

### ❌ NOGO: Don't Use @Transactional on Private Methods

```java
// ❌ BAD: @Transactional doesn't work on private methods (Spring uses proxies)
@Transactional
private void updateUserStatus(User user) {
    // Transaction won't work!
}

// ✅ GOOD: Make it public or protected, or move to service
@Transactional
public void updateUserStatus(User user) {
    // Works correctly
}
```

### ❌ NOGO: Don't Ignore Validation

```java
// ❌ BAD: No validation
@PostMapping("/users")
public User createUser(@RequestBody CreateUserRequest request) {
    return userService.createUser(request);
}

// ✅ GOOD: Always validate
@PostMapping("/users")
public ResponseEntity<UserDto> createUser(@Valid @RequestBody CreateUserRequest request) {
    return ResponseEntity.ok(userService.createUser(request));
}
```

### ❌ NOGO: Don't Use Raw SQL Without Parameterization

```java
// ❌ BAD: SQL injection risk (though JPA handles this, be careful with native queries)
@Query(value = "SELECT * FROM users WHERE email = '" + email + "'", nativeQuery = true)
User findByEmail(String email);

// ✅ GOOD: Use parameters
@Query(value = "SELECT * FROM users WHERE email = :email", nativeQuery = true)
User findByEmail(@Param("email") String email);
```

### ❌ NOGO: Don't Commit Secrets or Sensitive Data

- Never commit `.env` files
- Never commit `application-prod.yml` with real credentials
- Use environment variables or secret management
- Use `.gitignore` properly

---

## Additional Resources

- [Spring Boot Reference Documentation](https://docs.spring.io/spring-boot/docs/current/reference/html/)
- [Spring Data JPA Documentation](https://docs.spring.io/spring-data/jpa/docs/current/reference/html/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Effective Java by Joshua Bloch](https://www.oracle.com/java/technologies/effective-java.html)

---

## Code Review Checklist

Before submitting code for review, ensure:

- [ ] All tests pass
- [ ] Code follows naming conventions
- [ ] No hardcoded values (use configuration)
- [ ] Proper error handling implemented
- [ ] Input validation in place
- [ ] No security vulnerabilities (SQL injection, XSS, etc.)
- [ ] Proper logging (no System.out.println)
- [ ] DTOs used instead of entities in controllers
- [ ] Transactions used appropriately
- [ ] No N+1 query problems
- [ ] Proper HTTP status codes
- [ ] Appropriate design patterns applied
- [ ] Layers properly separated (Controller → Service → Repository)
- [ ] Dependency injection used correctly
- [ ] Documentation/comments where needed
- [ ] No secrets committed

---

**Last Updated**: 2024
**Version**: 1.0

