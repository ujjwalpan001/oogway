import pytest
from unittest.mock import AsyncMock, patch
from app.agent.skills.ship30 import run_ship30_skill, SHIP30_SYSTEM
from app.agent.skills.artifact_gen import run_artifact_skill, _extract_title


@pytest.mark.asyncio
async def test_ship30_calls_agent_complete():
    mock_output = "# 5 Growth Lessons\n\nHook line here.\n" + "Content " * 200
    mock_agent = AsyncMock()
    mock_agent.complete.return_value = mock_output

    with patch("app.agent.skills.ship30.get_agent", return_value=mock_agent):
        result = await run_ship30_skill("growth loops", "some transcript context")

    assert result == mock_output
    mock_agent.complete.assert_called_once()
    call_args = mock_agent.complete.call_args
    assert "growth loops" in call_args[0][0][0]["content"]
    assert call_args[0][1] == SHIP30_SYSTEM


@pytest.mark.asyncio
async def test_ship30_raises_on_agent_failure():
    mock_agent = AsyncMock()
    mock_agent.complete.side_effect = RuntimeError("API error")

    with patch("app.agent.skills.ship30.get_agent", return_value=mock_agent):
        with pytest.raises(RuntimeError, match="API error"):
            await run_ship30_skill("topic", "context")


@pytest.mark.asyncio
async def test_artifact_skill_extracts_markdown_title():
    content = "# My Awesome Growth Framework\n\nSome content here."
    mock_agent = AsyncMock()
    mock_agent.complete.return_value = content

    with patch("app.agent.skills.artifact_gen.get_agent", return_value=mock_agent):
        title, result = await run_artifact_skill("growth framework", "markdown", "context")

    assert title == "My Awesome Growth Framework"
    assert result == content


@pytest.mark.asyncio
async def test_artifact_skill_extracts_html_title():
    content = "<!DOCTYPE html><html><head><title>Growth Report</title></head><body></body></html>"
    mock_agent = AsyncMock()
    mock_agent.complete.return_value = content

    with patch("app.agent.skills.artifact_gen.get_agent", return_value=mock_agent):
        title, _ = await run_artifact_skill("growth report", "html", "context")

    assert title == "Growth Report"


def test_extract_title_fallback():
    title = _extract_title("No title line here", "markdown")
    assert title == "Generated Artifact"


def test_extract_title_markdown():
    content = "# My Title\n\nBody text"
    assert _extract_title(content, "markdown") == "My Title"
