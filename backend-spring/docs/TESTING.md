# Testing Guide

This document describes the testing strategy, test structure, and how to run tests for the Spring Boot backend.

## Table of Contents

1. [Test Structure](#test-structure)
2. [Test Types](#test-types)
3. [Running Tests](#running-tests)
4. [Test Coverage](#test-coverage)
5. [Writing New Tests](#writing-new-tests)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [Test History](#test-history)

---

## Test Structure

Tests are organized to mirror the main source structure:

```
src/test/java/com/short5/
├── controller/          # Controller tests (WebMvcTest)
├── service/              # Service tests (Unit tests with Mockito)
├── repository/           # Repository tests (DataJpaTest)
└── security/             # Security/JWT tests
```

---

## Test Types

### 1. Unit Tests (Service Layer)

Service tests use Mockito to mock dependencies:

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    @Mock
    private UserRepository userRepository;
    
    @InjectMocks
    private UserService userService;
    
    @Test
    void shouldGetUserProfile() {
        // Test implementation
    }
}
```

**Coverage:**
- ✅ `AuthServiceTest` - Registration, login, token refresh, vote merging
- ✅ `UserServiceTest` - User profile, videos, liked videos
- ✅ `VideoServiceTest` - Video CRUD, voting, sharing, views
- ✅ `FeedServiceTest` - Feed generation, recommendation algorithm
- ✅ `ReportServiceTest` - Report creation and validation
- ✅ `VideoProcessingServiceTest` - Video processing integration

### 2. Controller Tests (WebMvcTest)

Controller tests use MockMvc to test HTTP endpoints:

```java
@WebMvcTest(AuthController.class)
class AuthControllerTest {
    @Autowired
    private MockMvc mockMvc;
    
    @MockBean
    private AuthService authService;
    
    @Test
    void shouldRegisterUser() throws Exception {
        // Test HTTP endpoint
    }
}
```

**Coverage:**
- ✅ `AuthControllerTest` - Authentication endpoints
- ✅ `VideoControllerTest` - Video endpoints
- ✅ `FeedControllerTest` - Feed endpoint
- ✅ `RootControllerTest` - Root and health endpoints
- ✅ `InternalControllerTest` - Internal endpoints for callbacks

### 3. Repository Tests (DataJpaTest)

Repository tests use in-memory H2 database:

```java
@DataJpaTest
class UserRepositoryTest {
    @Autowired
    private TestEntityManager entityManager;
    
    @Autowired
    private UserRepository userRepository;
    
    @Test
    void shouldSaveAndFindUser() {
        // Test repository methods
    }
}
```

**Coverage:**
- ✅ `UserRepositoryTest` - User repository operations

### 4. Security Tests

JWT and security functionality tests:

```java
@ExtendWith(MockitoExtension.class)
class JwtServiceTest {
    @Test
    void shouldGenerateAndValidateToken() {
        // Test JWT operations
    }
}
```

**Coverage:**
- ✅ `JwtServiceTest` - Token generation, validation, extraction

---

## Running Tests

### Run All Tests

```bash
mvn test
```

### Run Specific Test Class

```bash
mvn test -Dtest=AuthServiceTest
```

### Run Tests with Coverage

```bash
mvn test jacoco:report
```

### Run Tests in IDE

- **IntelliJ IDEA**: Right-click on test class → Run
- **Eclipse**: Right-click on test class → Run As → JUnit Test
- **VS Code**: Use Java Test Runner extension

---

## Test Configuration

Test configuration is in `src/test/resources/application-test.yml`:

- Uses H2 in-memory database (no PostgreSQL required)
- Uses test JWT secret
- Uses temporary directory for file uploads
- Reduced logging levels

---

## Test Coverage Goals

- **Services**: 80%+ coverage
- **Controllers**: 70%+ coverage
- **Repositories**: 60%+ coverage
- **Security**: 90%+ coverage

---

## Writing New Tests

### Service Test Template

```java
@ExtendWith(MockitoExtension.class)
class MyServiceTest {
    @Mock
    private MyRepository repository;
    
    @InjectMocks
    private MyService service;
    
    @Test
    void shouldDoSomething() {
        // Given
        when(repository.findById(any())).thenReturn(Optional.of(entity));
        
        // When
        Result result = service.doSomething(id);
        
        // Then
        assertThat(result).isNotNull();
        verify(repository).findById(id);
    }
}
```

### Controller Test Template

```java
@WebMvcTest(MyController.class)
class MyControllerTest {
    @Autowired
    private MockMvc mockMvc;
    
    @MockBean
    private MyService service;
    
    @Test
    void shouldHandleRequest() throws Exception {
        when(service.doSomething(any())).thenReturn(result);
        
        mockMvc.perform(get("/api/v1/endpoint"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.field").value("expected"));
    }
}
```

---

## Best Practices

1. **Arrange-Act-Assert (AAA) Pattern**
   - Arrange: Set up test data and mocks
   - Act: Execute the method under test
   - Assert: Verify the results

2. **Test Naming**
   - Use descriptive names: `shouldReturnUserWhenIdExists()`
   - Follow pattern: `should[ExpectedBehavior]When[StateUnderTest]()`

3. **Mock External Dependencies**
   - Mock repositories, external services
   - Don't mock the class under test

4. **Test Edge Cases**
   - Null values
   - Empty collections
   - Invalid inputs
   - Error conditions

5. **Keep Tests Independent**
   - Each test should be able to run in isolation
   - Don't rely on test execution order

6. **Exception Testing**
   - Use specific exception type assertions
   - Verify exception messages
   - Test proper exception hierarchy

7. **Async Testing**
   - Use `CompletableFuture.join()` for async operations
   - Use `Thread.sleep()` for async method execution time
   - Proper timeout handling

---

## Troubleshooting

### Tests Failing with Database Errors

- Ensure H2 dependency is in `pom.xml`
- Check `application-test.yml` configuration
- Verify test database is in-memory

### Tests Failing with Security Errors

- Use `@WithMockUser` for authenticated endpoints
- Use `@WithMockUser(roles = "ADMIN")` for admin endpoints
- Add `@AutoConfigureMockMvc(addFilters = false)` if needed
- Exclude auto-configurations: `SecurityAutoConfiguration`, `DataSourceAutoConfiguration`, `HibernateJpaAutoConfiguration`

### Tests Failing with File Upload Errors

- Check temporary directory permissions
- Verify `uploadDir` is set correctly in test config
- Clean up test files after tests

### ApplicationContext Loading Issues

If `@WebMvcTest` is trying to load full application context:

1. **Exclude Auto-Configurations:**
   ```java
   @WebMvcTest(controllers = MyController.class,
       excludeAutoConfiguration = {
           SecurityAutoConfiguration.class,
           DataSourceAutoConfiguration.class,
           HibernateJpaAutoConfiguration.class
       })
   ```

2. **Add Security Mocks:**
   ```java
   @MockBean
   private JwtService jwtService;
   
   @MockBean
   private CustomUserDetailsService userDetailsService;
   ```

3. **Disable Security Filters:**
   ```java
   @AutoConfigureMockMvc(addFilters = false)
   ```

---

## Test History

### Test Summary

#### Service Tests (Unit Tests with Mockito)

1. **AuthServiceTest** - 8 test cases
   - User registration (success, username exists, email exists)
   - User login (success, user not found, wrong password, inactive user)
   - Anonymous vote merging on registration

2. **UserServiceTest** - 4 test cases
   - Get current user profile
   - Get user videos
   - Get liked videos
   - Empty liked videos list

3. **VideoServiceTest** - 9+ test cases
   - Get video details
   - Video not found
   - Upload video
   - Invalid file format
   - Vote on video
   - Record view
   - Share video
   - Delete video
   - Unauthorized deletion

4. **FeedServiceTest** - 4 test cases
   - Get feed for authenticated user
   - Get feed for anonymous user
   - Exclude liked videos from feed
   - Empty feed

5. **ReportServiceTest** - 5 test cases
   - Create video report
   - Create user report
   - Target not found
   - Self-reporting prevention
   - Duplicate report prevention

6. **VideoProcessingServiceTest** - 6 test cases
   - Trigger video processing successfully
   - Handle processing task submission failure
   - Handle video not found
   - Handle processing complete successfully
   - Handle processing complete failure
   - Handle processing complete with video not found

#### Controller Tests (WebMvcTest)

1. **AuthControllerTest** - 5 test cases
2. **VideoControllerTest** - 5 test cases
3. **FeedControllerTest** - 2 test cases
4. **RootControllerTest** - 2 test cases
5. **InternalControllerTest** - 3 test cases

#### Repository Tests (DataJpaTest)

1. **UserRepositoryTest** - 5 test cases

#### Security Tests

1. **JwtServiceTest** - 7 test cases

### Test Updates History

#### Custom Exception Migration

All tests have been updated to use custom exceptions:
- `ResourceNotFoundException` for "not found" errors
- `BadRequestException` for validation and business logic errors
- `ForbiddenException` for authorization errors

#### Service Dependencies

- `VideoServiceTest` updated with `VideoProcessingService` mock dependency
- All service tests updated to verify async operations correctly

### Known Issues and Fixes

1. **Missing Import in InternalControllerTest**
   - **Error:** `cannot find symbol: method verify()`
   - **Fix:** Added missing static import: `import static org.mockito.Mockito.verify;`

2. **ApplicationContext Loading Issues**
   - **Problem:** `@WebMvcTest` trying to load full application context
   - **Fix:** Excluded auto-configurations and added security mocks

---

## Continuous Integration

Tests should run automatically on:
- Pull requests
- Before merging to main
- On every commit (optional)

---

## Next Steps

- [ ] Add integration tests with TestContainers
- [ ] Add performance tests
- [ ] Add contract tests (API compatibility)
- [ ] Set up code coverage reporting (JaCoCo)
- [ ] Add mutation testing

---

**Last Updated**: 2024  
**Test Framework**: JUnit 5 + Mockito  
**Test Database**: H2 in-memory

