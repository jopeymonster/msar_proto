# Contributing Guidelines

These rules apply to **all contributions**, human or AI.

## Branching & PRs
- AI agents submit PRs into their dedicated branches (e.g., `codex`, `ai-security`).
- Human contributors submit PRs directly into `develop`.
- No contributions go directly into `main`.
- Promotion path:
  - AI branches → develop
  - Human PRs → develop
  - develop → main

## Code Standards
- Use Python 3.11+.
- Follow PEP8 formatting.
- Write clean, maintainable, and well-commented code.
- Use descriptive names for variables, functions, and branches.
- **No emojis are allowed in code, commit messages, or PR descriptions.**

## Docstring Guidelines

All functions, classes, and modules must include **docstrings** to clearly describe their purpose, inputs, and outputs.  
We follow the **Google style docstring** format for consistency across the project.

## Format Example

```python
def add_numbers(a: int, b: int) -> int:
    """
    Adds two integers together.

    Args:
        a (int): The first number.
        b (int): The second number.

    Returns:
        int: The sum of `a` and `b`.

    Example:
        >>> add_numbers(2, 3)
        5
    """
    return a + b
```

## Commits
- Commit messages should be imperative (e.g., "Add new validator" not "Added new validator").
- Keep commits scoped and focused.

## Testing
- Run `pytest` locally before submitting a PR.
- No failing tests or linting errors.
- Add or update tests when introducing new functionality or fixing bugs.

## Repository Hygiene
To keep the repository clean and consistent:

- **Do not commit**:
  - Virtual environments (e.g., `venv/`, `.venv/`, `ENV/`, `gads/`)
  - Cache directories (`.ruff_cache/`, `.pytest_cache/`, `.cache/`)
  - OS-specific junk (`.DS_Store`, `.idea/`, `.vscode/`)
  - Build/distribution artifacts (`dist/`, `build/`, `*.egg-info/`)

- Follow the `.gitignore` file — if you’re not sure whether something should be tracked, ask before committing.

- Sensitive or auth-related files must **never** be committed:
  - `*secret*`, `*cred*`, `*authorization*`

