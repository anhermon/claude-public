# Python Coding Patterns

## EAFP over LBYL for attribute access

Prefer `try/except` over `hasattr` chains — more robust, handles `None` mid-chain, avoids race conditions.

```python
# Avoid
if hasattr(agent, "config") and agent.config.adapters:
    process_adapters(agent)

# Prefer
try:
    if agent.config.adapters:
        process_adapters(agent)
except AttributeError:
    pass
```

## Protocols for interface contracts

Use `typing.Protocol` instead of implicit duck typing or ABC inheritance when a function requires a specific shape. Enables mypy without forcing inheritance.

```python
from typing import Protocol

class HasName(Protocol):
    name: str

def get_item_name(item: HasName) -> str:
    return item.name

# Works with any object that has name: str — no inheritance needed
class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

get_item_name(User(name="Claude", email="claude@example.com"))  # passes static analysis
```

## No path hacks

Never use `sys.path.append()` with relative paths. Use proper package structure or install in editable mode (`pip install -e .`).
