# AI Agent Rules for Spring Boot Development

This file contains rules and guidelines for AI agents working on the Short5 Platform Spring Boot backend. These rules are derived from `SPRING_BOOT_BEST_PRACTICES.md` and should be strictly followed.

## Quick Reference

**Project**: Short5 Platform Backend  
**Framework**: Spring Boot 3.2.0  
**Java Version**: 17  
**Build System**: Maven  
**Package**: `com.short5`  
**Reference Document**: `SPRING_BOOT_BEST_PRACTICES.md`

---

## Maven Project Structure (Essential for All Developers)

### Standard Directory Layout

```
backend-spring/
├── pom.xml                    # Maven build file
├── src/
│   ├── main/
│   │   ├── java/              # ← YOUR JAVA CODE GOES HERE
│   │   │   └── com/short5/    # Package structure starts here
│   │   └── resources/         # ← CONFIGURATION FILES GO HERE
│   │       └── application.yml
│   └── test/
│       ├── java/              # ← YOUR TESTS GO HERE
│       └── resources/         # ← TEST CONFIGURATION GOES HERE
└── target/                    # Build output (auto-generated, don't commit)
```

### Key Rules:
1. **Source Code**: Always in `src/main/java/com/short5/`
2. **Configuration**: Always in `src/main/resources/`
3. **Tests**: Always in `src/test/java/com/short5/`
4. **Main Class**: Must be in root package `com.short5` (not in sub-package)

### Common Mistakes to Avoid:
- ❌ Putting Java files in root directory
- ❌ Putting application.yml in root directory
- ❌ Creating non-standard directories
- ❌ Putting main class in sub-package

---

## Core Principles

1. **Separation of Concerns**: Controllers → Services → Repositories
2. **Dependency Injection**: Always use constructor injection
3. **DTO Pattern**: Never expose entities directly in APIs
4. **Validation**: Always validate input
5. **Error Handling**: Use custom exceptions and global handlers
6. **Security First**: Hash passwords, validate input, use parameterized queries
7. **Testability**: Write testable code with proper mocking
8. **Spring Boot Conventions**: Follow framework conventions

---

## Mandatory Code Patterns

### 1. Service Class Template

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
            .orElseThrow(() -> new EntityNotFoundException("Entity not found: " + id));
    }
    
    @Transactional
    public EntityDto create(CreateEntityRequest request) {
        // Validation
        if (entityRepository.existsByUniqueField(request.getUniqueField())) {
            throw new EntityAlreadyExistsException("Entity already exists");
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

### 2. Controller Template

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
    
    @PutMapping("/{id}")
    public ResponseEntity<EntityDto> updateEntity(
            @PathVariable Long id,
            @Valid @RequestBody UpdateEntityRequest request) {
        return ResponseEntity.ok(entityService.update(id, request));
    }
    
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteEntity(@PathVariable Long id) {
        entityService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
```

### 3. Repository Template

```java
@Repository
public interface EntityRepository extends JpaRepository<Entity, Long> {
    Optional<Entity> findByUniqueField(String uniqueField);
    boolean existsByUniqueField(String uniqueField);
    
    @Query("SELECT e FROM Entity e WHERE e.status = :status AND e.createdAt > :date")
    List<Entity> findActiveAfter(@Param("status") String status, @Param("date") LocalDateTime date);
    
    @EntityGraph(attributePaths = {"relatedEntities"})
    Optional<Entity> findByIdWithRelations(Long id);
}
```

### 4. DTO Templates

```java
// Request DTO
@Data
@NoArgsConstructor
@AllArgsConstructor
public class CreateEntityRequest {
    @NotBlank(message = "Field is required")
    @Size(min = 3, max = 100, message = "Field must be between 3 and 100 characters")
    private String field;
    
    @NotBlank
    @Email(message = "Invalid email format")
    private String email;
}

// Response DTO
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class EntityDto {
    private Long id;
    private String field;
    private String email;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
```

### 5. Entity Template

```java
@Entity
@Table(name = "entities")
@Getter
@Setter
@NoArgsConstructor
@EntityListeners(AuditingEntityListener.class)
@EqualsAndHashCode(onlyExplicitlyIncluded = true)
public class Entity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @EqualsAndHashCode.Include
    private Long id;
    
    @Column(nullable = false, unique = true)
    private String uniqueField;
    
    @OneToMany(mappedBy = "entity", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    private List<RelatedEntity> relatedEntities = new ArrayList<>();
    
    @CreatedDate
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;
    
    @LastModifiedDate
    @Column(nullable = false)
    private LocalDateTime updatedAt;
    
    @Column(nullable = false)
    private boolean deleted = false;
}
```

### 6. Exception Template

```java
public class EntityNotFoundException extends RuntimeException {
    public EntityNotFoundException(String message) {
        super(message);
    }
    
    public EntityNotFoundException(String message, Throwable cause) {
        super(message, cause);
    }
}
```

### 7. Global Exception Handler Template

```java
@ControllerAdvice
@Slf4j
public class GlobalExceptionHandler {
    
    @ExceptionHandler(EntityNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleEntityNotFound(EntityNotFoundException ex) {
        log.warn("Entity not found: {}", ex.getMessage());
        ErrorResponse error = ErrorResponse.builder()
            .code("ENTITY_NOT_FOUND")
            .message(ex.getMessage())
            .timestamp(LocalDateTime.now())
            .build();
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
    }
    
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidationErrors(MethodArgumentNotValidException ex) {
        Map<String, String> errors = new HashMap<>();
        ex.getBindingResult().getFieldErrors().forEach(error ->
            errors.put(error.getField(), error.getDefaultMessage())
        );
        
        ErrorResponse error = ErrorResponse.builder()
            .code("VALIDATION_ERROR")
            .message("Validation failed")
            .errors(errors)
            .timestamp(LocalDateTime.now())
            .build();
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }
    
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGenericException(Exception ex) {
        log.error("Unexpected error", ex);
        ErrorResponse error = ErrorResponse.builder()
            .code("INTERNAL_ERROR")
            .message("An unexpected error occurred")
            .timestamp(LocalDateTime.now())
            .build();
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }
}
```

---

## Decision Tree: What Pattern to Use?

### When creating a new feature:

1. **Need to access database?**
   - ✅ Create Repository interface extending `JpaRepository<Entity, Long>`
   - ✅ Use Spring Data JPA query methods or `@Query`

2. **Need business logic?**
   - ✅ Create Service class with `@Service`
   - ✅ Use `@Transactional` for write operations
   - ✅ Use `@Transactional(readOnly = true)` for reads

3. **Need HTTP endpoint?**
   - ✅ Create Controller with `@RestController`
   - ✅ Use `@RequestMapping("/api/v1/...")`
   - ✅ Always use DTOs, never entities
   - ✅ Use `@Valid` on request DTOs

4. **Need custom validation?**
   - ✅ Add Bean Validation annotations to DTOs
   - ✅ Create custom validators if needed

5. **Need error handling?**
   - ✅ Create custom exception class
   - ✅ Add handler to `GlobalExceptionHandler`

6. **Need to cache?**
   - ✅ Use `@Cacheable` on service methods
   - ✅ Use `@CacheEvict` when updating

7. **Need async processing?**
   - ✅ Use `@Async` on service methods
   - ✅ Return `CompletableFuture<>`

8. **Need events?**
   - ✅ Create event class extending `ApplicationEvent`
   - ✅ Use `ApplicationEventPublisher` to publish
   - ✅ Create `@EventListener` methods

---

## Code Quality Checklist

Before submitting code, verify:

### Structure
- [ ] Follows package structure (controller/service/repository/dto/model)
- [ ] Layers are properly separated
- [ ] No business logic in controllers
- [ ] No business logic in repositories

### Dependency Injection
- [ ] Uses constructor injection with `@RequiredArgsConstructor`
- [ ] No field injection with `@Autowired` (except optional dependencies)
- [ ] Dependencies are marked as `final`

### DTOs
- [ ] Separate DTOs for request and response
- [ ] Controllers use DTOs, not entities
- [ ] Mapping between entities and DTOs in service layer

### Validation
- [ ] Request DTOs have validation annotations
- [ ] Controllers use `@Valid` on `@RequestBody`
- [ ] Custom validation for complex rules

### Error Handling
- [ ] Custom exceptions for domain errors
- [ ] Global exception handler configured
- [ ] Proper HTTP status codes
- [ ] No stack traces exposed to clients

### Database
- [ ] `@Transactional` on service write methods
- [ ] `@Transactional(readOnly = true)` on read methods
- [ ] Uses `Optional<>` for nullable returns
- [ ] Lazy loading by default
- [ ] No N+1 query problems

### Security
- [ ] Passwords are hashed (BCrypt)
- [ ] Input validation in place
- [ ] No SQL injection risks
- [ ] Proper CORS configuration

### Testing
- [ ] Unit tests for services
- [ ] Integration tests for controllers
- [ ] Repository tests with `@DataJpaTest`

### Code Style
- [ ] Uses Lombok appropriately
- [ ] No `@Data` on JPA entities
- [ ] Proper logging with SLF4J
- [ ] No hardcoded values
- [ ] Follows naming conventions

---

## Common Scenarios & Solutions

### Scenario 1: Create a new REST endpoint

**Steps:**
1. Create Request DTO with validation
2. Create Response DTO
3. Add repository method if needed
4. Add service method with business logic
5. Add controller endpoint
6. Add exception handling if needed
7. Write tests

### Scenario 2: Add a new entity with relationships

**Steps:**
1. Create Entity class with proper annotations
2. Create Repository interface
3. Create DTOs (Request/Response)
4. Create Service with CRUD operations
5. Create Controller with endpoints
6. Handle cascade operations properly
7. Write tests

### Scenario 3: Add caching to existing service

**Steps:**
1. Enable caching in configuration
2. Add `@Cacheable` to read methods
3. Add `@CacheEvict` to update/delete methods
4. Configure cache names
5. Test cache behavior

### Scenario 4: Add async processing

**Steps:**
1. Enable async in configuration (`@EnableAsync`)
2. Create async service method with `@Async`
3. Return `CompletableFuture<>`
4. Handle exceptions in async context
5. Test async behavior

### Scenario 5: Add event-driven functionality

**Steps:**
1. Create event class extending `ApplicationEvent`
2. Publish event using `ApplicationEventPublisher`
3. Create `@EventListener` methods
4. Use `@Async` if needed
5. Test event flow

---

## Anti-Patterns to Avoid

1. ❌ **God Object**: Service doing too much
   - ✅ Split into focused services

2. ❌ **Anemic Domain Model**: Entities with no behavior
   - ✅ Add business methods to entities when appropriate

3. ❌ **Tight Coupling**: Direct dependencies between layers
   - ✅ Use interfaces and dependency injection

4. ❌ **Magic Numbers/Strings**: Hardcoded values
   - ✅ Use constants or configuration

5. ❌ **Primitive Obsession**: Using primitives instead of value objects
   - ✅ Create value objects for domain concepts

6. ❌ **Feature Envy**: Method uses more features of another class than its own
   - ✅ Move method to appropriate class

---

## Testing Patterns

### Unit Test Template

```java
@ExtendWith(MockitoExtension.class)
class EntityServiceTest {
    @Mock
    private EntityRepository entityRepository;
    
    @InjectMocks
    private EntityService entityService;
    
    @Test
    void shouldCreateEntitySuccessfully() {
        // Given
        CreateEntityRequest request = new CreateEntityRequest("test");
        Entity savedEntity = new Entity(1L, "test");
        
        when(entityRepository.existsByUniqueField("test")).thenReturn(false);
        when(entityRepository.save(any(Entity.class))).thenReturn(savedEntity);
        
        // When
        EntityDto result = entityService.create(request);
        
        // Then
        assertThat(result.getField()).isEqualTo("test");
        verify(entityRepository).save(any(Entity.class));
    }
}
```

### Integration Test Template

```java
@SpringBootTest
@AutoConfigureMockMvc
class EntityControllerIntegrationTest {
    @Autowired
    private MockMvc mockMvc;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    @Test
    void shouldCreateEntity() throws Exception {
        CreateEntityRequest request = new CreateEntityRequest("test");
        
        mockMvc.perform(post("/api/v1/entities")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.field").value("test"));
    }
}
```

---

## Reference

For detailed examples and explanations, refer to:
- `SPRING_BOOT_BEST_PRACTICES.md` - Complete best practices guide
- Spring Boot Documentation: https://docs.spring.io/spring-boot/docs/current/reference/html/
- Spring Data JPA Documentation: https://docs.spring.io/spring-data/jpa/docs/current/reference/html/

---

**Last Updated**: 2024  
**Version**: 1.0

