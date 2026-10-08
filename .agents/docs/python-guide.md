# Python guide

Rules for all Python code in `ai_reviewer/` and `tests/`.

## Code structure

- Use OOP: put functionality inside classes.
- When the task targets a class, change only that class. Module-level error classes for it are allowed; other new classes are not.
- Change method signatures only as a last resort. On change, update all callers and note the change in the summary.
- No abbreviations in names, except common ones (`id`, `url`, `json`).

## Methods

- Fit a method in 24 lines of 80 characters (120 at most).
- Separate queries from commands (methods that change object or system state).
- Public methods take at most 2 parameters; more only as a last resort.
- Every method has a docstring.
- Type every method fully; use built-in generics (`list`, `dict`), not `typing.List`, `typing.Dict`.
- Keep comments minimal; they explain why, not what.

## Docstrings

```python
def foo(self, param1: str, param2: str = "") -> str:
    """
    Short summary of what the method does.

    :param param1: description1
    :param param2: description2

    :raises UserNotFoundError: when it is raised

    :return: description
    """
```

## Errors

- Define error classes at module level, next to the class, not nested inside it.
- Errors a class can raise are part of its public contract; declare them explicitly.
- Raise only for situations whose correctness the class owns.
- Raise typed errors that name the cause of the problem, not how it was detected. No generic `Exception`.
- Do not suppress errors. Catch only to add meaning or to recover correctly; otherwise let them propagate.
- When catching, add context: at which step the problem happened.
- Convert errors from external resources into errors of the class's own level.
- A method either succeeds or raises, never leaving the object inconsistent. State-changing methods are atomic or roll back on error.
- The interface or abstract class defines the error types. Implementations add details but never change the type.
