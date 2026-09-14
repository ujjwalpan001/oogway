from app.agent.router import get_agent
from app.logging_config import get_logger

logger = get_logger(__name__)

ARTIFACT_SYSTEM = """You are a document generation assistant. Based on the conversation and sources provided, generate the requested document.

Rules:
- For Markdown artifacts: Use clean markdown with proper headers, tables, and code blocks where appropriate.
- For HTML artifacts: Generate COMPLETE, self-contained HTML/CSS. Include all styles inline or in a <style> tag. No external URLs.
- Do not include any explanation before or after the document.
- Start your output immediately with the document content.
- For HTML: start with <!DOCTYPE html>
- For Markdown: start with # Title

Generate high-quality, professional output. If the user asked for a framework, roadmap, comparison table, or report — structure it visually."""


async def run_artifact_skill(request: str, artifact_type: str, context: str) -> tuple[str, str]:
    agent = get_agent()
    type_hint = "an HTML document" if artifact_type == "html" else "a Markdown document"
    messages = [
        {
            "role": "user",
            "content": f"Generate {type_hint} for: {request}\n\nContext from Lenny's Podcast:\n{context}",
        }
    ]
    try:
        content = await agent.complete(messages, ARTIFACT_SYSTEM)

        title = _extract_title(content, artifact_type)
        logger.info("artifact_generated", type=artifact_type, content_len=len(content))
        return title, content
    except Exception as exc:
        logger.error("artifact_skill_failed", error=str(exc))
        raise


def _extract_title(content: str, artifact_type: str) -> str:
    lines = content.strip().split("\n")
    for line in lines[:5]:
        stripped = line.strip()
        if artifact_type == "markdown" and stripped.startswith("# "):
            return stripped[2:].strip()
        if artifact_type == "html" and "<title>" in stripped.lower():
            import re
            match = re.search(r"<title>(.*?)</title>", stripped, re.IGNORECASE)
            if match:
                return match.group(1).strip()
    return "Generated Artifact"
