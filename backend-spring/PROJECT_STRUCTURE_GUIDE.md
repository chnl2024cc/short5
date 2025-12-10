# Spring Boot Project Structure Guide

**For developers new to Spring Boot or Maven/Gradle project structure**

This guide explains where to put files in a Spring Boot project. This is essential knowledge for all developers.

---

## 📁 Complete Project Structure Overview

```
backend-spring/                          ← Project root directory
│
├── 📄 pom.xml                           ← Maven build configuration (defines dependencies)
├── 📄 README.md                         ← Project documentation
├── 📄 .gitignore                        ← Files to ignore in Git
├── 📄 Dockerfile                        ← Docker configuration (optional)
│
├── 📁 src/                              ← Source directory (ALL your code goes here)
│   │
│   ├── 📁 main/                         ← Main application code
│   │   │
│   │   ├── 📁 java/                     ← ⭐ YOUR JAVA CODE GOES HERE
│   │   │   └── com/
│   │   │       └── short5/              ← Your package (matches your domain)
│   │   │           ├── 📄 Short5Application.java  ← Main class (MUST be here)
│   │   │           ├── 📁 config/       ← Configuration classes
│   │   │           ├── 📁 controller/   ← REST API endpoints
│   │   │           ├── 📁 service/      ← Business logic
│   │   │           ├── 📁 repository/   ← Database access
│   │   │           ├── 📁 entity/       ← Database entities
│   │   │           ├── 📁 dto/          ← Data Transfer Objects
│   │   │           ├── 📁 exception/    ← Custom exceptions
│   │   │           ├── 📁 security/     ← Security config
│   │   │           └── 📁 util/         ← Utility classes
│   │   │
│   │   └── 📁 resources/                ← ⭐ CONFIGURATION FILES GO HERE
│   │       ├── 📄 application.yml       ← Main configuration
│   │       ├── 📄 application-dev.yml  ← Development config
│   │       ├── 📄 application-prod.yml  ← Production config
│   │       ├── 📁 static/              ← Static files (CSS, JS, images)
│   │       └── 📁 templates/           ← HTML templates (if using)
│   │
│   └── 📁 test/                         ← Test code
│       │
│       ├── 📁 java/                     ← ⭐ YOUR TESTS GO HERE
│       │   └── com/
│       │       └── short5/              ← Same package structure as main
│       │           ├── 📁 controller/   ← Controller tests
│       │           ├── 📁 service/      ← Service tests
│       │           └── 📁 repository/   ← Repository tests
│       │
│       └── 📁 resources/                ← ⭐ TEST CONFIGURATION GOES HERE
│           ├── 📄 application-test.yml ← Test configuration
│           └── 📁 test-data/           ← Test data files
│
└── 📁 target/                           ← Build output (auto-generated, don't commit)
    ├── classes/                         ← Compiled Java classes
    └── *.jar                            ← Generated JAR files
```

---

## 🎯 Quick Reference: Where Does This File Go?

| What You're Creating | Where It Goes | Example Path |
|---------------------|---------------|--------------|
| **Java class** (Controller, Service, etc.) | `src/main/java/com/short5/` | `src/main/java/com/short5/controller/UserController.java` |
| **Configuration file** (application.yml) | `src/main/resources/` | `src/main/resources/application.yml` |
| **Test class** | `src/test/java/com/short5/` | `src/test/java/com/short5/service/UserServiceTest.java` |
| **Test configuration** | `src/test/resources/` | `src/test/resources/application-test.yml` |
| **Static files** (images, CSS) | `src/main/resources/static/` | `src/main/resources/static/images/logo.png` |
| **HTML templates** | `src/main/resources/templates/` | `src/main/resources/templates/index.html` |
| **Build file** | Project root | `pom.xml` (at root level) |

---

## 📝 Detailed Explanation

### 1. Source Code Directory: `src/main/java/`

**Purpose**: All your Java source code (.java files)

**Structure**:
```
src/main/java/com/short5/
├── Short5Application.java    ← Main class (MUST be in root package)
├── config/                   ← Configuration classes
├── controller/              ← REST controllers
├── service/                 ← Business logic
├── repository/              ← Database access
├── entity/                  ← Database entities
├── dto/                     ← Data Transfer Objects
├── exception/               ← Custom exceptions
├── security/                ← Security configuration
└── util/                    ← Utility classes
```

**Rules**:
- ✅ All `.java` files go here
- ✅ Package structure starts from `com/short5/`
- ✅ Main class must be in root package (`com.short5`)
- ❌ Never put Java files in root directory
- ❌ Never put Java files in `src/main/resources/`

### 2. Resources Directory: `src/main/resources/`

**Purpose**: Configuration files, static files, templates

**Structure**:
```
src/main/resources/
├── application.yml           ← Main configuration (REQUIRED)
├── application-dev.yml      ← Development profile
├── application-prod.yml     ← Production profile
├── static/                  ← Static files (optional)
│   ├── css/
│   ├── js/
│   └── images/
└── templates/               ← Templates (optional)
    └── index.html
```

**Rules**:
- ✅ Configuration files (`.yml`, `.properties`) go here
- ✅ Static files (CSS, JS, images) go in `static/` subdirectory
- ✅ Templates go in `templates/` subdirectory
- ❌ Never put Java files here
- ❌ Never put configuration in root directory

### 3. Test Directory: `src/test/java/`

**Purpose**: All your test code

**Structure**:
```
src/test/java/com/short5/
├── controller/
│   └── UserControllerTest.java
├── service/
│   └── UserServiceTest.java
└── repository/
    └── UserRepositoryTest.java
```

**Rules**:
- ✅ Mirror the structure of `src/main/java/`
- ✅ Test class name: `{ClassName}Test.java`
- ✅ Same package structure as main code
- ❌ Don't put tests in `src/main/java/`

### 4. Test Resources: `src/test/resources/`

**Purpose**: Test-specific configuration and test data

**Structure**:
```
src/test/resources/
├── application-test.yml     ← Test configuration
└── test-data/               ← Test data files
    └── sample-users.json
```

---

## ⚠️ Common Mistakes (Don't Do These!)

### ❌ Mistake 1: Java files in wrong location
```
backend-spring/
├── UserController.java      ← WRONG! Should be in src/main/java/
└── src/
    └── main/
        └── java/
```

### ❌ Mistake 2: Configuration in wrong location
```
backend-spring/
├── application.yml          ← WRONG! Should be in src/main/resources/
└── src/
    └── main/
        └── resources/
```

### ❌ Mistake 3: Main class in sub-package
```java
// WRONG!
package com.short5.app;  // Sub-package

@SpringBootApplication
public class Short5Application {
    // Spring won't scan properly!
}

// CORRECT!
package com.short5;  // Root package

@SpringBootApplication
public class Short5Application {
    // Spring scans from here
}
```

### ❌ Mistake 4: Creating non-standard directories
```
backend-spring/
├── java/                    ← WRONG! Use src/main/java/
├── config/                  ← WRONG! Use src/main/resources/
└── tests/                   ← WRONG! Use src/test/java/
```

---

## 🎓 Why This Structure?

### Maven Standard Directory Layout

Spring Boot uses Maven (or Gradle), which follows a **standard directory layout**. This structure is:

1. **Universal**: All Maven/Gradle projects use it
2. **Tool-friendly**: IDEs and build tools expect it
3. **Conventional**: Other developers will understand it
4. **Required**: Spring Boot expects files in these locations

### How Spring Boot Finds Files

- **Java Classes**: Spring scans `src/main/java/` for `@Component`, `@Service`, `@Repository`, etc.
- **Configuration**: Spring looks for `application.yml` in `src/main/resources/`
- **Tests**: Maven runs tests from `src/test/java/`
- **Static Files**: Spring serves files from `src/main/resources/static/` at URL `/`

---

## 📋 Checklist: Creating a New Feature

When creating a new feature, use this checklist:

- [ ] Create entity class in `src/main/java/com/short5/entity/`
- [ ] Create repository interface in `src/main/java/com/short5/repository/`
- [ ] Create DTOs in `src/main/java/com/short5/dto/request/` and `dto/response/`
- [ ] Create service class in `src/main/java/com/short5/service/`
- [ ] Create controller class in `src/main/java/com/short5/controller/`
- [ ] Create exception classes in `src/main/java/com/short5/exception/`
- [ ] Create unit tests in `src/test/java/com/short5/service/`
- [ ] Create integration tests in `src/test/java/com/short5/controller/`
- [ ] Update `src/main/resources/application.yml` if needed

---

## 🔍 How to Verify Your Structure

### Check 1: Main Application Class
```bash
# Should be at:
src/main/java/com/short5/Short5Application.java
```

### Check 2: Configuration File
```bash
# Should be at:
src/main/resources/application.yml
```

### Check 3: Package Structure
```bash
# All Java files should be under:
src/main/java/com/short5/
```

### Check 4: Test Structure
```bash
# All test files should be under:
src/test/java/com/short5/
```

---

## 📚 Additional Resources

- **Maven Standard Directory Layout**: https://maven.apache.org/guides/introduction/introduction-to-the-standard-directory-layout.html
- **Spring Boot Project Structure**: See `SPRING_BOOT_BEST_PRACTICES.md`
- **AI Rules**: See `.cursorrules` and `AI_RULES.md`

---

## 💡 Quick Tips

1. **Use your IDE**: Most IDEs (IntelliJ, Eclipse, VS Code) create this structure automatically
2. **Follow conventions**: Don't create custom directories - use the standard layout
3. **Check existing code**: Look at existing files to see where they're located
4. **Ask if unsure**: When in doubt, ask a senior developer or check this guide

---

**Remember**: 
- Source code → `src/main/java/`
- Configuration → `src/main/resources/`
- Tests → `src/test/java/`
- Main class → Root package (`com.short5`)

---

**Last Updated**: 2024  
**Version**: 1.0

