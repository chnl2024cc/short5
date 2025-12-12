# Testing Guide

This document describes the testing strategy and how to run tests for the Spring Boot backend.

## Test Structure

Tests are organized to mirror the main source structure:

```
src/test/java/com/short5/
├── controller/          # Controller tests (WebMvcTest)
├── service/              # Service tests (Unit tests with Mockito)
├── repository/           # Repository tests (DataJpaTest)
└── security/             # Security/JWT tests
```

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

## Test Configuration

Test configuration is in `src/test/resources/application-test.yml`:

- Uses H2 in-memory database (no PostgreSQL required)
- Uses test JWT secret
- Uses temporary directory for file uploads
- Reduced logging levels

## Test Coverage Goals

- **Services**: 80%+ coverage
- **Controllers**: 70%+ coverage
- **Repositories**: 60%+ coverage
- **Security**: 90%+ coverage

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

## Continuous Integration

Tests should run automatically on:
- Pull requests
- Before merging to main
- On every commit (optional)

## Troubleshooting

### Tests Failing with Database Errors

- Ensure H2 dependency is in `pom.xml`
- Check `application-test.yml` configuration
- Verify test database is in-memory

### Tests Failing with Security Errors

- Use `@WithMockUser` for authenticated endpoints
- Use `@WithMockUser(roles = "ADMIN")` for admin endpoints
- Add `@AutoConfigureMockMvc(addFilters = false)` if needed

### Tests Failing with File Upload Errors

- Check temporary directory permissions
- Verify `uploadDir` is set correctly in test config
- Clean up test files after tests

## Next Steps

- [ ] Add integration tests with TestContainers
- [ ] Add performance tests
- [ ] Add contract tests (API compatibility)
- [ ] Set up code coverage reporting
- [ ] Add mutation testing

