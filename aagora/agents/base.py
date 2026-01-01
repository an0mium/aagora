"""
Base utilities for creating agents.
"""

from typing import Literal

def create_agent(
    model_type: Literal["codex", "claude", "openai"],
    name: str = None,
    role: str = "proposer",
    model: str = None,
):
    """Factory function to create agents by type."""
    from aagora.agents.cli_agents import CodexAgent, ClaudeAgent, OpenAIAgent

    if model_type == "codex":
        return CodexAgent(
            name=name or "codex",
            model=model or "gpt-5.2-codex",
            role=role,
        )
    elif model_type == "claude":
        return ClaudeAgent(
            name=name or "claude",
            model=model or "claude-sonnet-4",
            role=role,
        )
    elif model_type == "openai":
        return OpenAIAgent(
            name=name or "openai",
            model=model or "gpt-4o",
            role=role,
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
