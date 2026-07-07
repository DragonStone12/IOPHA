# Ruff & Mypy Linting Rules

## Table of Contents

| #   | Section                                         | Description                          |
| --- | ----------------------------------------------- | ------------------------------------ |
| 1   | [Overview](#overview)                           | Threat categories and scope          |
| 2   | [Ruff Plugin Breakdown](#ruff-plugin-breakdown) | Detailed rules for each plugin       |
| 3   | [Mypy Configuration](#mypy-configuration)       | Type checking configuration          |
| 4   | [CI Integration](#ci-integration)               | Pre-commit hooks, GitHub Actions     |
| 5   | [Handling Violations](#handling-violations)     | Inline ignores, tuning, adding rules |
| 6   | [Complementary Tools](#complementary-tools)     | Defense-in-depth tooling             |

---

## Overview

The IOPHA backend uses Ruff and Mypy as primary static analysis tools. Ruff provides fast linting with multiple rule sets including security checks, while Mypy enforces strict type safety. These checks run via Husky pre-commit hooks before commits reach CI and on every pull request via GitHub Actions.

### What This Guards Against

| Threat Category              | What It Catches                                          |
| ---------------------------- | -------------------------------------------------------- |
| **Syntax errors**            | Undefined variables, unused imports, unreachable code    |
| **Code style**               | Line length, naming conventions, formatting issues       |
| **Security vulnerabilities** | Hardcoded passwords, weak cryptography, shell injection  |
| **Logic bugs**               | Assert used for runtime guarantees, mutable default args |
| **Type safety**              | Missing type hints, incompatible type assignments        |
| **Code complexity**          | Overly complex functions, duplicated code patterns       |

---

## Ruff Plugin Breakdown

### 1. Pyflakes (F) — Syntax and Logic Errors

**Focus:** Catches undefined names, unused imports, and other logical errors.

| Rule | Severity  | What It Does                                                                                      |
| ---- | --------- | ------------------------------------------------------------------------------------------------- |
| F401 | **error** | Module imported but unused. Prevents dead code and potential security issues from unused imports. |
| F402 | **error** | Import alias used for module with same name. Prevents confusing code.                             |
| F403 | **error** | `from module import *` used. Prevents namespace pollution and hidden dependencies.                |
| F404 | **error** | Import alias used for module with same name as global. Prevents shadowing.                        |
| F405 | **error** | Name may be undefined or defined from star imports.                                               |
| F541 | **error** | F-string without any placeholders.                                                                |
| F631 | **error** | Lambda assignment to variable. Use `def` instead.                                                 |
| F821 | **error** | Undefined name. Catches typos and missing imports.                                                |
| F822 | **error** | Undefined name in `__all__`.                                                                      |
| F841 | **error** | Local variable assigned but never used.                                                           |

### 2. Pycodestyle (E/W) — Style Guide Enforcement

**Focus:** Enforces PEP 8 style conventions for readable code.

| Rule | Severity  | What It Does                                            |
| ---- | --------- | ------------------------------------------------------- |
| E501 | **error** | Line too long (default 88 chars). Enforces readability. |
| E225 | **error** | Missing whitespace around operator.                     |
| E231 | **error** | Missing whitespace after ',', ';', or ':'.              |
| E251 | **error** | Unexpected spaces around keyword/parameter equals.      |
| W291 | **error** | Trailing whitespace. Avoids whitespace-only diffs.      |
| W292 | **error** | No newline at end of file.                              |
| W293 | **error** | Blank line contains whitespace.                         |

### 3. isort (I) — Import Sorting

**Focus:** Ensures consistent import ordering for maintainable code.

| Rule | Severity  | What It Does                                                 |
| ---- | --------- | ------------------------------------------------------------ |
| I001 | **error** | Import statements not sorted. Maintains consistent ordering. |
| I002 | **error** | Missing import from `__future__` imports.                    |

### 4. Pydocstyle (N) — Docstring Conventions

**Focus:** Enforces docstring presence and formatting.

| Rule | Severity  | What It Does                          |
| ---- | --------- | ------------------------------------- |
| D100 | **error** | Missing docstring in public module.   |
| D101 | **error** | Missing docstring in public class.    |
| D102 | **error** | Missing docstring in public method.   |
| D103 | **error** | Missing docstring in public function. |
| D104 | **error** | Missing docstring in public package.  |
| D105 | **error** | Missing docstring in magic method.    |
| D107 | **error** | Missing docstring in `__init__`.      |

### 5. Bandit Security (S) — Security Vulnerability Detection

**Focus:** Detects security issues and unsafe patterns in Python code.

| Rule | Severity  | What It Does                                                                |
| ---- | --------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| S101 | **warn**  | `assert` used for runtime guarantees. Disabled in tests via pyproject.toml. |
| S102 | **error** | `exec` used. Potential code injection vector.                               |
| S103 | **warn**  | Missing permission on file open.                                            |
| S104 | **error** | File code starts with shebang. Could execute accidentally.                  |
| S105 | **error** | hardcoded-password-string                                                   | Ignored (S105) via pyproject.toml — too many false positives in test data. |
| S106 | **error** | hardcoded-password-func-arg                                                 | Ignored (S106) via pyproject.toml — too many false positives.              |
| S107 | **error** | hardcoded-password-default                                                  | Ignored (S107) via pyproject.toml — too many false positives.              |
| S303 | **error** | `hashlib` used with weak hash function. Use SHA-256+ for security.          |
| S304 | **error** | `ssl` wrapped socket with no default verification.                          |
| S305 | **error** | `ssl` wrapped socket with no host verification.                             |
| S306 | **error** | `subprocess` module called with shell=True. Command injection risk.         |
| S307 | **error** | `subprocess` module called with partially sanitized input.                  |
| S308 | **error** | `mark_safe` used with partially sanitized input. XSS risk.                  |
| S310 | **error** | `urllib` call with url that isn't validated. SSRF risk.                     |
| S404 | **warn**  | Use of `telnetlib` detected. Insecure protocol.                             |
| S603 | **warn**  | `subprocess` module without shell=False.                                    |
| S605 | **warn**  | `subprocess` module called with shell=True.                                 |

### 6. Bugbear (B) — Bug and Design Problem Detection

**Focus:** Catches common bugs and design problems in Python code.

| Rule | Severity  | What It Does                                                      |
| ---- | --------- | ----------------------------------------------------------------- |
| B002 | **error** | Loop variable overridden in loop.                                 |
| B003 | **error** | Mutable default argument used.                                    |
| B004 | **error** | Default mutable argument in function call.                        |
| B005 | **warn**  | `strip()` called on dict-like without argument.                   |
| B006 | **error** | Mutable default argument for mutable type.                        |
| B007 | **error** | Loop variable used without `break` or `return`.                   |
| B008 | **error** | Function call in argument defaults. Prevents unexpected behavior. |
| B009 | **error** | `getattr` with constant string. Use direct access.                |
| B010 | **error** | `setattr` with constant string. Use direct assignment.            |
| B011 | **error** | `assert` with empty message.                                      |
| B012 | **error** | Jump after `assert` statement.                                    |
| B013 | **error** | `while` loop with constant condition.                             |
| B014 | **error** | Assertion on constant value.                                      |
| B015 | **error** | `pointless-statement` — expression statement with no effect.      |
| B016 | **error** | `raise` inside `try` without `except`.                            |
| B017 | **error** | `assert` with `assertRaises` in unittest.                         |
| B018 | **warn**  | Found useless `return` at end of function.                        |
| B019 | **error** | `cached` attribute set on class without `lru_cache`.              |
| B020 | **error** | `exec` used without arguments.                                    |
| B021 | **error** | `f-string` without placeholders in logging.                       |
| B022 | **error** | Function signature with default value before `*args`.             |
| B023 | **error** | Function definition with mutable default argument.                |
| B024 | **error** | Abstract method without `raise NotImplementedError`.              |
| B025 | **error** | Duplicate exception handler.                                      |
| B026 | **error** | `except` handler with extraneous parentheses.                     |
| B027 | **warn**  | Empty method in abstract class.                                   |
| B028 | **warn**  | `no-value` for `raise` in exception handler.                      |
| B030 | **error** | `except` handler with extraneous parentheses.                     |

### 7. Pylint Refactoring (PLR) — Code Refactoring Detection

**Focus:** Identifies code that should be refactored for maintainability.

| Rule    | Severity  | What It Does                                              |
| ------- | --------- | --------------------------------------------------------- |
| PLR0124 | **error** | `condition` with overlapping branches.                    |
| PLR0202 | **error** | Class method has no `self` argument.                      |
| PLR0206 | **error** | Property with parameters.                                 |
| PLR0402 | **error** | Module imported only for type. Use `TYPE_CHECKING` block. |
| PLR0911 | **error** | Too many return statements. Refactor for clarity.         |
| PLR0912 | **error** | Too many branches. Refactor for clarity.                  |
| PLR0913 | **error** | Too many arguments. Refactor to reduce complexity.        |
| PLR0915 | **error** | Too many statements. Refactor for maintainability.        |
| PLR1702 | **error** | No-else-return — unnecessary `else` after `return`.       |

---

## Mypy Configuration

**Focus:** Enforces static type checking for type safety.

Configuration in `IOPHA-backend/pyproject.toml`:

| Option                     | Value | Purpose                                               |
| -------------------------- | ----- | ----------------------------------------------------- |
| `warn_return_any`          | true  | Warns when returning `Any` from function.             |
| `warn_unused_configs`      | true  | Warns about unused config options.                    |
| `disallow_untyped_defs`    | true  | Requires type annotations on all functions.           |
| `disallow_incomplete_defs` | true  | Requires all function arguments to be typed.          |
| `check_untyped_defs`       | true  | Type-checks function bodies even without annotations. |
| `no_implicit_optional`     | true  | Disallows implicit Optional without `Optional[]`.     |
| `warn_redundant_casts`     | true  | Warns when casting to the same type.                  |
| `warn_unused_ignores`      | true  | Warns about unused `# type: ignore` comments.         |
| `show_error_codes`         | true  | Shows error code in output for easier lookup.         |

### Type Stub Dependencies

The following type stubs are installed to provide type hints for third-party libraries:

| Package            | Purpose                             |
| ------------------ | ----------------------------------- |
| `types-requests`   | Type hints for `requests` library   |
| `types-setuptools` | Type hints for `setuptools` library |

---

## CI Integration

### Pre-Commit Hooks (Husky)

Local enforcement is handled by Husky. The hook scripts live in `.husky/`:

- `.husky/pre-commit` — For staged `IOPHA-backend/` Python files it runs `ruff check --fix` and `ruff format`, re-stages the result, then runs a **verifying** `ruff check` and `ruff format --check` that blocks the commit if anything remains. The frontend equivalent is `npx lint-staged`.
- `.husky/pre-push` — Mirrors CI: `npm run test:changed` (frontend) plus `ruff check IOPHA-backend/` and `ruff format --check IOPHA-backend/`.

`ruff` is resolved defensively by the hook (`command -v ruff` → `venv/bin/ruff` → `python3 -m ruff`) so the gate works whether ruff is global or inside a virtualenv. If ruff cannot be found, the hook fails loudly instead of silently committing.

> **Note:** `mypy` and `bandit` run in CI (`ci-backend.yml`), not in the pre-commit hook, to keep commits fast.

### GitHub Actions

The `ci-backend.yml` workflow runs all checks on every push and pull request to `main`:

| Job         | Tool      | Description                         |
| ----------- | --------- | ----------------------------------- |
| ruff        | Ruff      | Linting check                       |
| ruff-format | Ruff      | Formatting check                    |
| mypy        | Mypy      | Static type checking                |
| bandit      | Bandit    | Security scanning with SARIF upload |
| pip-audit   | pip-audit | Dependency vulnerability audit      |

---

## Handling Violations

### Intentional Patterns

When a rule flags a pattern that is intentional and safe, use an inline disable comment:

```python
# type: ignore[arg-type]
dangerous_var = some_func()
```

For Ruff, use `# noqa: S105` to disable specific rules on specific lines.

### Tuning Thresholds

Rule ignores are configured in `IOPHA-backend/pyproject.toml`:

```toml
[tool.ruff.lint]
ignore = ["S105", "S106", "S107"]
```

### Adding New Rules

When adding new rules from Ruff plugins:

1. Set to `"warn"` first to assess impact
2. Review existing violations and fix or suppress intentionally
3. Upgrade to `"error"` once the codebase is clean
4. Update this documentation with the new rule

---

## Complementary Tools

| Tool        | Scope           | What Ruff/Mypy Miss                                      |
| ----------- | --------------- | -------------------------------------------------------- |
| `bandit`    | Python security | Runtime security patterns not covered by static analysis |
| `pip-audit` | Dependencies    | Known vulnerabilities in installed packages              |
| CodeQL      | Data flow       | Taint analysis across function boundaries                |
| ESLint      | Frontend        | Frontend-specific security and style patterns            |
