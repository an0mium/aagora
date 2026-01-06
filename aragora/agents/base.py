"""
Base utilities for creating agents.
"""

import re
from typing import Literal, Union

from aragora.core import Critique, Message


# Context window limits (in characters, ~4 chars per token)
# Use 60% of available window to leave room for response
MAX_CONTEXT_CHARS = 120_000  # ~30k tokens, safe for most models
MAX_MESSAGE_CHARS = 20_000   # Individual message truncation limit


class CritiqueMixin:
    """Mixin providing shared critique parsing and context building methods.

    Used by both CLIAgent and APIAgent to avoid code duplication.
    """

    # Required attributes (provided by subclasses)
    name: str

    def _build_context_prompt(
        self,
        context: list[Message] | None = None,
        truncate: bool = False,
        sanitize_fn=None,
    ) -> str:
        """Build context from previous messages.

        Args:
            context: List of previous messages
            truncate: Whether to truncate long messages/context (CLI agents should use True)
            sanitize_fn: Optional function to sanitize content (for CLI safety)

        Returns:
            Formatted context string
        """
        if not context:
            return ""

        if not truncate:
            # Simple mode (API agents) - no truncation
            context_str = "\n\n".join([
                f"[Round {m.round}] {m.role} ({m.agent}):\n{m.content}"
                for m in context[-10:]
            ])
            return f"\n\nPrevious discussion:\n{context_str}\n\n"

        # Truncation mode (CLI agents) - handle large contexts
        messages = []
        total_chars = 0

        for m in context[-10:]:
            content = m.content
            if sanitize_fn:
                content = sanitize_fn(content)

            # Truncate individual messages that are too long
            if len(content) > MAX_MESSAGE_CHARS:
                half = MAX_MESSAGE_CHARS // 2 - 50
                content = (
                    content[:half] +
                    f"\n\n[... {len(m.content) - MAX_MESSAGE_CHARS} chars truncated ...]\n\n" +
                    content[-half:]
                )

            msg_str = f"[Round {m.round}] {m.role} ({m.agent}):\n{content}"

            # Check if adding this message would exceed total limit
            if total_chars + len(msg_str) > MAX_CONTEXT_CHARS:
                remaining = MAX_CONTEXT_CHARS - total_chars - 100
                if remaining > 500:
                    msg_str = msg_str[:remaining] + "\n[... truncated ...]"
                    messages.append(msg_str)
                break

            messages.append(msg_str)
            total_chars += len(msg_str) + 4

        context_str = "\n\n".join(messages)
        return f"\n\nPrevious discussion:\n{context_str}\n\n"

    def _parse_critique(self, response: str, target_agent: str, target_content: str) -> Critique:
        """Parse a critique response into structured format.

        Extracts issues, suggestions, and severity from natural language critique.
        """
        issues = []
        suggestions = []
        severity = 0.5
        reasoning = ""

        lines = response.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            lower = line.lower()
            if 'issue' in lower or 'problem' in lower or 'concern' in lower:
                current_section = 'issues'
            elif 'suggest' in lower or 'recommend' in lower or 'improvement' in lower:
                current_section = 'suggestions'
            elif 'severity' in lower:
                match = re.search(r'(\d+\.?\d*)', line)
                if match:
                    try:
                        severity = min(1.0, max(0.0, float(match.group(1))))
                        if severity > 1:
                            severity = severity / 10  # Handle 0-10 scale
                    except (ValueError, TypeError):
                        pass
            elif line.startswith(('-', '*', '•')):
                item = line.lstrip('-*• ').strip()
                if current_section == 'issues':
                    issues.append(item)
                elif current_section == 'suggestions':
                    suggestions.append(item)
                else:
                    # Default to issues
                    issues.append(item)

        # If no structured extraction, use the whole response
        if not issues and not suggestions:
            sentences = [s.strip() for s in response.replace('\n', ' ').split('.') if s.strip()]
            mid = len(sentences) // 2
            issues = sentences[:mid] if sentences else ["See full response"]
            suggestions = sentences[mid:] if len(sentences) > mid else []
            reasoning = response[:500]
        else:
            reasoning = response[:500]

        return Critique(
            agent=self.name,
            target_agent=target_agent,
            target_content=target_content[:200],
            issues=issues[:5],  # Limit to 5 issues
            suggestions=suggestions[:5],  # Limit to 5 suggestions
            severity=severity,
            reasoning=reasoning,
        )


AgentType = Literal[
    # CLI-based
    "codex", "claude", "openai", "gemini-cli", "grok-cli", "qwen-cli", "deepseek-cli", "kilocode",
    # API-based (direct)
    "gemini", "ollama", "anthropic-api", "openai-api", "grok",
    # API-based (via OpenRouter)
    "deepseek", "deepseek-r1", "llama", "mistral", "openrouter",
]


def create_agent(
    model_type: AgentType,
    name: str | None = None,
    role: str = "proposer",
    model: str | None = None,
    api_key: str | None = None,
):
    """
    Factory function to create agents by type.

    Args:
        model_type: Type of agent to create:
            - "codex": OpenAI Codex CLI
            - "claude": Claude CLI (claude-code)
            - "openai": OpenAI CLI
            - "gemini-cli": Google Gemini CLI
            - "grok-cli": xAI Grok CLI
            - "qwen-cli": Alibaba Qwen Code CLI
            - "deepseek-cli": Deepseek CLI
            - "gemini": Google Gemini API
            - "ollama": Local Ollama API
            - "anthropic-api": Direct Anthropic API
            - "openai-api": Direct OpenAI API
            - "grok": xAI Grok API
            - "deepseek": DeepSeek V3 via OpenRouter
            - "deepseek-r1": DeepSeek R1 (reasoning) via OpenRouter
            - "llama": Llama 3.3 70B via OpenRouter
            - "mistral": Mistral Large via OpenRouter
            - "openrouter": Generic OpenRouter (specify model)
        name: Agent name (defaults to model_type)
        role: Agent role ("proposer", "critic", "synthesizer")
        model: Specific model to use (optional)
        api_key: API key for API-based agents (optional, uses env vars)

    Returns:
        Agent instance
    """
    # CLI-based agents
    if model_type == "codex":
        from aragora.agents.cli_agents import CodexAgent
        return CodexAgent(
            name=name or "codex",
            model=model or "gpt-5.2-codex",
            role=role,
        )
    elif model_type == "claude":
        from aragora.agents.cli_agents import ClaudeAgent
        return ClaudeAgent(
            name=name or "claude",
            model=model or "claude-sonnet-4",
            role=role,
        )
    elif model_type == "openai":
        from aragora.agents.cli_agents import OpenAIAgent
        return OpenAIAgent(
            name=name or "openai",
            model=model or "gpt-4o",
            role=role,
        )
    elif model_type == "gemini-cli":
        from aragora.agents.cli_agents import GeminiCLIAgent
        return GeminiCLIAgent(
            name=name or "gemini",
            model=model or "gemini-3-pro-preview",
            role=role,
        )
    elif model_type == "grok-cli":
        from aragora.agents.cli_agents import GrokCLIAgent
        return GrokCLIAgent(
            name=name or "grok",
            model=model or "grok-4",
            role=role,
        )
    elif model_type == "qwen-cli":
        from aragora.agents.cli_agents import QwenCLIAgent
        return QwenCLIAgent(
            name=name or "qwen",
            model=model or "qwen3-coder",
            role=role,
        )
    elif model_type == "deepseek-cli":
        from aragora.agents.cli_agents import DeepseekCLIAgent
        return DeepseekCLIAgent(
            name=name or "deepseek",
            model=model or "deepseek-v3",
            role=role,
        )
    elif model_type == "kilocode":
        from aragora.agents.cli_agents import KiloCodeAgent
        return KiloCodeAgent(
            name=name or "kilocode",
            role=role,
        )

    # API-based agents
    elif model_type == "gemini":
        from aragora.agents.api_agents import GeminiAgent
        return GeminiAgent(
            name=name or "gemini",
            model=model or "gemini-3-pro-preview",
            role=role,
            api_key=api_key,
        )
    elif model_type == "ollama":
        from aragora.agents.api_agents import OllamaAgent
        return OllamaAgent(
            name=name or "ollama",
            model=model or "llama3.2",
            role=role,
        )
    elif model_type == "anthropic-api":
        from aragora.agents.api_agents import AnthropicAPIAgent
        return AnthropicAPIAgent(
            name=name or "claude-api",
            model=model or "claude-sonnet-4-20250514",
            role=role,
            api_key=api_key,
        )
    elif model_type == "openai-api":
        from aragora.agents.api_agents import OpenAIAPIAgent
        return OpenAIAPIAgent(
            name=name or "openai-api",
            model=model or "gpt-4o",
            role=role,
            api_key=api_key,
        )
    elif model_type == "grok":
        from aragora.agents.api_agents import GrokAgent
        return GrokAgent(
            name=name or "grok",
            model=model or "grok-3",
            role=role,
        )

    # OpenRouter-based agents
    elif model_type == "deepseek":
        from aragora.agents.api_agents import DeepSeekAgent
        return DeepSeekAgent(
            name=name or "deepseek",
            role=role,
        )
    elif model_type == "deepseek-r1":
        from aragora.agents.api_agents import DeepSeekReasonerAgent
        return DeepSeekReasonerAgent(
            name=name or "deepseek-r1",
            role=role,
        )
    elif model_type == "llama":
        from aragora.agents.api_agents import LlamaAgent
        return LlamaAgent(
            name=name or "llama",
            role=role,
        )
    elif model_type == "mistral":
        from aragora.agents.api_agents import MistralAgent
        return MistralAgent(
            name=name or "mistral",
            role=role,
        )
    elif model_type == "openrouter":
        from aragora.agents.api_agents import OpenRouterAgent
        return OpenRouterAgent(
            name=name or "openrouter",
            model=model or "deepseek/deepseek-v3.2",  # V3.2 latest
            role=role,
        )

    else:
        raise ValueError(
            f"Unknown model type: {model_type}. "
            f"Valid types: codex, claude, openai, gemini-cli, grok-cli, qwen-cli, deepseek-cli, "
            f"gemini, ollama, anthropic-api, openai-api, grok, deepseek, deepseek-r1, llama, mistral, openrouter"
        )


def list_available_agents() -> dict:
    """List all available agent types and their requirements."""
    return {
        "codex": {
            "type": "CLI",
            "requires": "codex CLI (npm install -g @openai/codex)",
            "env_vars": None,
        },
        "claude": {
            "type": "CLI",
            "requires": "claude CLI (npm install -g @anthropic-ai/claude-code)",
            "env_vars": None,
        },
        "openai": {
            "type": "CLI",
            "requires": "openai CLI (pip install openai)",
            "env_vars": "OPENAI_API_KEY",
        },
        "gemini-cli": {
            "type": "CLI",
            "requires": "gemini CLI (npm install -g @google/gemini-cli)",
            "env_vars": None,
        },
        "grok-cli": {
            "type": "CLI",
            "requires": "grok CLI (npm install -g grok-cli)",
            "env_vars": None,
        },
        "qwen-cli": {
            "type": "CLI",
            "requires": "qwen CLI (npm install -g @qwen-code/qwen-code)",
            "env_vars": None,
        },
        "deepseek-cli": {
            "type": "CLI",
            "requires": "deepseek CLI (pip install deepseek-cli)",
            "env_vars": "DEEPSEEK_API_KEY",
        },
        "gemini": {
            "type": "API",
            "requires": None,
            "env_vars": "GEMINI_API_KEY or GOOGLE_API_KEY",
        },
        "ollama": {
            "type": "API",
            "requires": "Ollama running locally (brew install ollama && ollama serve)",
            "env_vars": "OLLAMA_HOST (optional, defaults to localhost:11434)",
        },
        "anthropic-api": {
            "type": "API",
            "requires": None,
            "env_vars": "ANTHROPIC_API_KEY",
        },
        "openai-api": {
            "type": "API",
            "requires": None,
            "env_vars": "OPENAI_API_KEY",
        },
        "grok": {
            "type": "API",
            "requires": None,
            "env_vars": "XAI_API_KEY or GROK_API_KEY",
        },
        "deepseek": {
            "type": "API (OpenRouter)",
            "requires": None,
            "env_vars": "OPENROUTER_API_KEY",
            "description": "DeepSeek V3 - excellent for coding/math, very cost-effective",
        },
        "deepseek-r1": {
            "type": "API (OpenRouter)",
            "requires": None,
            "env_vars": "OPENROUTER_API_KEY",
            "description": "DeepSeek R1 - chain-of-thought reasoning model",
        },
        "llama": {
            "type": "API (OpenRouter)",
            "requires": None,
            "env_vars": "OPENROUTER_API_KEY",
            "description": "Llama 3.3 70B Instruct",
        },
        "mistral": {
            "type": "API (OpenRouter)",
            "requires": None,
            "env_vars": "OPENROUTER_API_KEY",
            "description": "Mistral Large",
        },
        "openrouter": {
            "type": "API (OpenRouter)",
            "requires": None,
            "env_vars": "OPENROUTER_API_KEY",
            "description": "Generic OpenRouter - specify model via 'model' parameter",
        },
    }
