name: designing-python-layered-architecture
description: Designs a production-ready layered architecture for Python desktop applications. Use when the user mentions layered architecture, clean structure, desktop app scaling, PySide, PyQt, Tkinter, or separation of concerns.
---

# Designing Python Layered Architecture for Desktop Apps

## When to use this skill

- User asks for layered architecture
- User is building a Python desktop app
- User mentions scaling, maintainability, clean structure
- User is using PySide, PyQt, Tkinter, or similar GUI frameworks
- User wants separation of concerns

---

## Architecture Overview

Standard 4-layer structure:

```

myapp/
├── main.py
├── presentation/
├── application/
├── domain/
├── infrastructure/
└── tests/

```

### Dependency Rule (Critical)

Dependencies flow inward only:

```

presentation → application → domain
infrastructure → application

````

Domain must never import:
- UI frameworks
- Database drivers
- HTTP libraries

---

## Workflow

### Step 1 — Identify Complexity

Checklist:

- [ ] Is there business logic?
- [ ] Is there a database or API?
- [ ] Will the app scale?
- [ ] Does UI need to be replaceable?

If mostly "yes" → Use layered architecture.

---

### Step 2 — Define Layer Responsibilities

#### Presentation
- Windows
- Dialogs
- Widgets
- User interaction only

No business logic.

#### Application
- Use cases
- Orchestration
- Transaction control
- Service coordination

#### Domain
- Entities
- Value objects
- Business rules
- Pure Python only

#### Infrastructure
- Database
- File system
- External APIs
- Logging
- Config

---

### Step 3 — Scaffold Project

Low freedom operation:

```bash
mkdir -p myapp/{presentation,application,domain,infrastructure,tests}
touch myapp/main.py
````

Optional deeper structure:

```bash
mkdir -p myapp/presentation/{windows,viewmodels}
mkdir -p myapp/application/services
mkdir -p myapp/domain/entities
mkdir -p myapp/infrastructure/{database,api}
```

---

## Implementation Pattern

### Presentation Example

```python
# presentation/login_window.py

class LoginWindow:
    def __init__(self, auth_service):
        self.auth_service = auth_service

    def on_login_clicked(self, username, password):
        result = self.auth_service.login(username, password)
        return result
```

---

### Application Example

```python
# application/services/auth_service.py

class AuthService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def login(self, username, password):
        user = self.user_repository.get_by_username(username)
        if not user:
            return False
        return user.verify_password(password)
```

---

### Domain Example

```python
# domain/entities/user.py

class User:
    def __init__(self, username, password_hash):
        self.username = username
        self.password_hash = password_hash

    def verify_password(self, password):
        return hash(password) == self.password_hash
```

---

### Infrastructure Example

```python
# infrastructure/database/user_repository.py

class UserRepository:
    def get_by_username(self, username):
        # database query here
        pass
```

---

## Validation Loop (Plan → Validate → Execute)

1. Plan architecture changes.
2. Validate imports:

   * Ensure domain has no external dependencies.
3. Execute changes.

Quick validation script:

```bash
grep -R "PySide\|PyQt\|requests\|sqlite3" domain/
```

If output exists → architecture violation.

---

## Error Handling

* Services should return structured results or raise domain-specific exceptions.
* Infrastructure errors must not leak raw DB exceptions to presentation.
* If unsure how to use a script:

```bash
python script_name.py --help
```

---

## Testing Strategy

* Test domain in isolation.
* Mock infrastructure in application tests.
* Avoid GUI testing unless necessary.

---

## Scalability Extensions

When the app grows:

* Add dependency injection container.
* Introduce event bus.
* Add plugin loader under infrastructure/plugins.
* Convert presentation to MVVM if needed.

---

## Resources

* presentation/
* application/services/
* domain/entities/
* infrastructure/database/
