"""
Skill Unit Tests
Tests the Ship 30 and Artifact Generation skills using mocked agents.
No real LLM calls are made — all agents are replaced with AsyncMock.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.agent.skills.ship30 import run_ship30_skill, SHIP30_SYSTEM
from app.agent.skills.artifact_gen import run_artifact_skill, _extract_title
from app.models import User

# ---------------------------------------------------------------------------
# Fake User for tests (skills now require a User object)
# ---------------------------------------------------------------------------

FAKE_USER = User(
    id="skill-test-user",
    email="skills@example.com",
    password_hash="fakehash",
)


# ---------------------------------------------------------------------------
# Ship 30 Skill
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ship30_calls_agent_complete():
    """ship30 skill should call agent.complete with the topic and correct system prompt."""
    mock_output = "# 5 Growth Lessons\n\nHook line here.\n" + "Content " * 200
    mock_agent = AsyncMock()
    mock_agent.complete.return_value = mock_output

    with patch("app.agent.skills.ship30.get_agent", return_value=mock_agent):
        result = await run_ship30_skill(FAKE_USER, "growth loops", "some transcript context")

    assert result == mock_output
    mock_agent.complete.assert_called_once()
    call_args = mock_agent.complete.call_args
    # First positional arg is the messages list; first message content contains the topic
    assert "growth loops" in call_args[0][0][0]["content"]
    # Second positional arg is the system prompt
    assert call_args[0][1] == SHIP30_SYSTEM


@pytest.mark.asyncio
async def test_ship30_includes_context_in_prompt():
    """ship30 skill should embed the RAG context into the user message."""
    mock_agent = AsyncMock()
    mock_agent.complete.return_value = "# Essay\n\nContent"

    context = "Brian Chesky said: do things that don't scale."

    with patch("app.agent.skills.ship30.get_agent", return_value=mock_agent):
        await run_ship30_skill(FAKE_USER, "founder mode", context)

    call_content = mock_agent.complete.call_args[0][0][0]["content"]
    assert context in call_content


@pytest.mark.asyncio
async def test_ship30_raises_on_agent_failure():
    """ship30 skill should propagate RuntimeError from the agent."""
    mock_agent = AsyncMock()
    mock_agent.complete.side_effect = RuntimeError("API error")

    with patch("app.agent.skills.ship30.get_agent", return_value=mock_agent):
        with pytest.raises(RuntimeError, match="API error"):
            await run_ship30_skill(FAKE_USER, "topic", "context")


# ---------------------------------------------------------------------------
# Artifact Generation Skill
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_artifact_skill_extracts_markdown_title():
    """Artifact skill should parse H1 header as the title for Markdown artifacts."""
    content = "# My Awesome Growth Framework\n\nSome content here."
    mock_agent = AsyncMock()
    mock_agent.complete.return_value = content

    with patch("app.agent.skills.artifact_gen.get_agent", return_value=mock_agent):
        title, result = await run_artifact_skill(FAKE_USER, "growth framework", "markdown", "context")

    assert title == "My Awesome Growth Framework"
    assert result == content


@pytest.mark.asyncio
async def test_artifact_skill_extracts_html_title():
    """Artifact skill should parse <title> tag as the document title for HTML artifacts."""
    content = "<!DOCTYPE html><html><head><title>Growth Report</title></head><body></body></html>"
    mock_agent = AsyncMock()
    mock_agent.complete.return_value = content

    with patch("app.agent.skills.artifact_gen.get_agent", return_value=mock_agent):
        title, _ = await run_artifact_skill(FAKE_USER, "growth report", "html", "context")

    assert title == "Growth Report"


@pytest.mark.asyncio
async def test_artifact_skill_raises_on_agent_failure():
    """Artifact skill should propagate exceptions from the underlying agent."""
    mock_agent = AsyncMock()
    mock_agent.complete.side_effect = RuntimeError("LLM timeout")

    with patch("app.agent.skills.artifact_gen.get_agent", return_value=mock_agent):
        with pytest.raises(RuntimeError, match="LLM timeout"):
            await run_artifact_skill(FAKE_USER, "report", "markdown", "ctx")


# ---------------------------------------------------------------------------
# Title Extraction (Pure Unit Tests — No mocks needed)
# ---------------------------------------------------------------------------

def test_extract_title_fallback():
    """_extract_title should return 'Generated Artifact' when no title is found."""
    title = _extract_title("No title line here", "markdown")
    assert title == "Generated Artifact"


def test_extract_title_markdown():
    """_extract_title should parse the first H1 heading from Markdown."""
    content = "# My Title\n\nBody text"
    assert _extract_title(content, "markdown") == "My Title"


def test_extract_title_html():
    """_extract_title should parse <title> tag from HTML content."""
    content = "<html><head><title>My HTML Title</title></head><body></body></html>"
    assert _extract_title(content, "html") == "My HTML Title"


def test_extract_title_ignores_h2():
    """_extract_title should not treat ## H2 headers as titles for markdown."""
    content = "## Section Header\n\nContent"
    title = _extract_title(content, "markdown")
    assert title == "Generated Artifact"
