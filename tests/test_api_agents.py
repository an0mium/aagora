"""
Tests for API agent implementations.

Tests agent_type attribute and basic agent structure without making API calls.
"""

import pytest
from unittest.mock import patch, MagicMock

from aragora.core import Agent


class TestAgentTypeAttribute:
    """Tests to ensure all agents have agent_type attribute."""

    def test_base_agent_has_agent_type(self):
        """Test base Agent class has agent_type attribute initialized."""
        # Create a concrete implementation for testing
        class ConcreteAgent(Agent):
            async def generate(self, prompt, context=None):
                return "test"

            async def critique(self, proposal, task, context=None):
                pass

        agent = ConcreteAgent("test", "model", "role")
        assert hasattr(agent, "agent_type")
        assert agent.agent_type == "unknown"

    def test_api_agent_base_has_agent_type(self):
        """Test APIAgent base class sets agent_type."""
        from aragora.agents.api_agents import APIAgent

        # Create a concrete implementation
        class ConcreteAPIAgent(APIAgent):
            async def generate(self, prompt, context=None):
                return "test"

            async def critique(self, proposal, task, context=None):
                pass

        agent = ConcreteAPIAgent("test", "model")
        assert hasattr(agent, "agent_type")
        assert agent.agent_type == "api"

    def test_gemini_agent_has_correct_type(self):
        """Test GeminiAgent has correct agent_type."""
        from aragora.agents.api_agents import GeminiAgent

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test"}):
            agent = GeminiAgent()

        assert agent.agent_type == "gemini"

    def test_anthropic_agent_has_correct_type(self):
        """Test AnthropicAPIAgent has correct agent_type."""
        from aragora.agents.api_agents import AnthropicAPIAgent

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test"}):
            agent = AnthropicAPIAgent()

        assert agent.agent_type == "anthropic"

    def test_openai_agent_has_correct_type(self):
        """Test OpenAIAPIAgent has correct agent_type."""
        from aragora.agents.api_agents import OpenAIAPIAgent

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test"}):
            agent = OpenAIAPIAgent()

        assert agent.agent_type == "openai"

    def test_grok_agent_has_correct_type(self):
        """Test GrokAgent has correct agent_type."""
        from aragora.agents.api_agents import GrokAgent

        with patch.dict("os.environ", {"XAI_API_KEY": "test"}):
            agent = GrokAgent()

        assert agent.agent_type == "grok"

    def test_ollama_agent_has_correct_type(self):
        """Test OllamaAgent has correct agent_type."""
        from aragora.agents.api_agents import OllamaAgent

        agent = OllamaAgent()
        assert agent.agent_type == "ollama"

    def test_openrouter_agent_has_correct_type(self):
        """Test OpenRouterAgent has correct agent_type."""
        from aragora.agents.api_agents import OpenRouterAgent

        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test"}):
            agent = OpenRouterAgent()

        assert agent.agent_type == "openrouter"

    def test_deepseek_agent_has_correct_type(self):
        """Test DeepSeekAgent has correct agent_type."""
        from aragora.agents.api_agents import DeepSeekAgent

        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test"}):
            agent = DeepSeekAgent()

        assert agent.agent_type == "deepseek"

    def test_deepseek_reasoner_agent_has_correct_type(self):
        """Test DeepSeekReasonerAgent has correct agent_type."""
        from aragora.agents.api_agents import DeepSeekReasonerAgent

        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test"}):
            agent = DeepSeekReasonerAgent()

        assert agent.agent_type == "deepseek-r1"

    def test_llama_agent_has_correct_type(self):
        """Test LlamaAgent has correct agent_type."""
        from aragora.agents.api_agents import LlamaAgent

        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test"}):
            agent = LlamaAgent()

        assert agent.agent_type == "llama"

    def test_mistral_agent_has_correct_type(self):
        """Test MistralAgent has correct agent_type."""
        from aragora.agents.api_agents import MistralAgent

        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test"}):
            agent = MistralAgent()

        assert agent.agent_type == "mistral"


class TestAgentInheritance:
    """Tests for agent class inheritance."""

    def test_gemini_inherits_from_api_agent(self):
        """Test GeminiAgent inherits from APIAgent."""
        from aragora.agents.api_agents import GeminiAgent, APIAgent

        assert issubclass(GeminiAgent, APIAgent)

    def test_anthropic_inherits_from_api_agent(self):
        """Test AnthropicAPIAgent inherits from APIAgent."""
        from aragora.agents.api_agents import AnthropicAPIAgent, APIAgent

        assert issubclass(AnthropicAPIAgent, APIAgent)

    def test_openrouter_inherits_from_api_agent(self):
        """Test OpenRouterAgent inherits from APIAgent."""
        from aragora.agents.api_agents import OpenRouterAgent, APIAgent

        assert issubclass(OpenRouterAgent, APIAgent)

    def test_deepseek_inherits_from_openrouter(self):
        """Test DeepSeekAgent inherits from OpenRouterAgent."""
        from aragora.agents.api_agents import DeepSeekAgent, OpenRouterAgent

        assert issubclass(DeepSeekAgent, OpenRouterAgent)


class TestAgentAttributes:
    """Tests for agent attributes."""

    def test_agent_has_name(self):
        """Test agent has name attribute."""
        from aragora.agents.api_agents import GeminiAgent

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test"}):
            agent = GeminiAgent(name="test-agent")

        assert agent.name == "test-agent"

    def test_agent_has_model(self):
        """Test agent has model attribute."""
        from aragora.agents.api_agents import GeminiAgent

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test"}):
            agent = GeminiAgent(model="gemini-2.0-flash")

        assert agent.model == "gemini-2.0-flash"

    def test_agent_has_role(self):
        """Test agent has role attribute."""
        from aragora.agents.api_agents import GeminiAgent

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test"}):
            agent = GeminiAgent(role="critic")

        assert agent.role == "critic"

    def test_agent_has_timeout(self):
        """Test agent has timeout attribute."""
        from aragora.agents.api_agents import GeminiAgent

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test"}):
            agent = GeminiAgent(timeout=60)

        assert agent.timeout == 60

    def test_agent_has_system_prompt(self):
        """Test agent can have system_prompt."""
        from aragora.agents.api_agents import GeminiAgent

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test"}):
            agent = GeminiAgent()
            agent.set_system_prompt("You are a helpful assistant.")

        assert agent.system_prompt == "You are a helpful assistant."


class TestAgentRepr:
    """Tests for agent string representation."""

    def test_agent_repr(self):
        """Test agent __repr__ method."""
        from aragora.agents.api_agents import GeminiAgent

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test"}):
            agent = GeminiAgent(name="test", role="proposer")

        repr_str = repr(agent)
        assert "GeminiAgent" in repr_str
        assert "test" in repr_str
        assert "proposer" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
