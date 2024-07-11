from __future__ import annotations


class CommandFailure(Exception):
    def __init__(self, command: str, failures: list[dict[str, str]]) -> None:
        self.command = command
        self.failures = failures

    def __str__(self) -> str:
        failures_lines = "\n".join(f"{failure['name']}: {failure['reason']}" for failure in self.failures)
        return f"Command '{self.command}' failed on:\n{failures_lines}"
