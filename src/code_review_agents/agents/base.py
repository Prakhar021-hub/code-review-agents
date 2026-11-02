from dataclasses import dataclass

from code_review_agents.llm import ask


@dataclass
class Agent:
    """A reviewer: a name plus a system prompt that defines its job."""

    name: str
    system_prompt: str

    def review(self, code: str) -> str:
        numbered = "\n".join(
            f"{i}: {line}" for i, line in enumerate(code.splitlines(), start=1)
        )
        return ask(self.system_prompt, "Review this code:\n\n" + numbered)