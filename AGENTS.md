# AGENTS.md

This repository supports AI contributions.  
All AI agents must also follow the [CONTRIBUTING.md](CONTRIBUTING.md) guidelines.

## Codex

### Branching
- All Codex-generated changes must target the `codex` branch.
- Temporary tasks are acceptable, but must be merged into `codex` first.
- Codex PRs should never target `develop` or `main` directly.
- After review, Codex changes are merged into `develop`.

### Development Flow
- The promotion path is: `codex → develop → main`.
- The `issues` branch is reserved for hotfixes.

### Standards
- Respect all rules in [CONTRIBUTING.md](CONTRIBUTING.md).
- Use Python 3.11+.
- Follow PEP8 formatting.
- Commit messages should be in imperative mood (e.g., "Add helper function", not "Added helper function").

### Styling Guidelines

#### Quoting and String Handling
- **Never** use backticks (\`) to wrap strings or comments in Python code.  
- Strings must always use **single quotes `'`** or **double quotes `"`**, depending on project style.  
  - Examples:  
    - `message = "Hello World"` → approved  
    - `message = 'Hello World'` → approved  
    - ``message = `Hello World``` → not approved  
- Backticks are only allowed when required for **Markdown formatting** (e.g., in README.md, documentation, or docstrings showing inline code).  
- Comments must also avoid backticks unless referencing inline code in Markdown.  
- This rule **extends PEP8**: backticks are treated as **invalid syntax** for any runtime string in Python.  
- **Enforcement:** Pull requests containing backticks in Python code (outside of Markdown/docstrings) will be rejected.  

#### Additional Styling and Character Regulations
- **Dashes:** Do not use em dashes (`—`).  
  - Use a standard single dash with whitespace as a conjoiner: `" - "`.  
  - Example: `"Option A - Option B"` (approved) vs `"Option A—Option B"` (not approved)  

- **Arrows:** Do not use Unicode arrows like (`→`) in code, strings, or descriptions.  
  - Use ASCII arrows with whitespace conjoiners: `" > "` for single steps, `" --> "` for mappings.  
  - Example: `"A --> B"` (approved) vs `"A → B"` (not approved)  

### Testing
- Run `pytest` before submitting PRs.
- No failing tests or lint errors allowed.
- Prefer test-driven updates when modifying critical functions.

### Repository Hygiene
- **Do not commit** caches, environment directories, or IDE-specific files:
  - `.ruff_cache/`, `.pytest_cache/`, `.cache/`
  - `venv/`, `.venv/`, `env/`, `ENV/`
  - `.DS_Store`, `.idea/`, `.vscode/`
- Do not commit build/distribution artifacts (`dist/`, `build/`, `*.egg-info/`).
- Sensitive/auth files (e.g., `*secret*`, `*cred*`, `*service-account.json`) must never be committed.
- Always respect `.gitignore`.

