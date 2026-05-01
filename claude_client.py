import logging

import anthropic

from config import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a senior software engineer conducting a pull request review. "
    "Analyze the provided diff and respond in this exact format:\n\n"
    "Summary: One sentence describing what this PR does.\n\n"
    "Issues Found:\n"
    "- [CRITICAL/WARNING/INFO] Description with line reference if applicable\n\n"
    "Suggestions:\n"
    "- Specific improvement with brief code example if needed\n\n"
    "Security Concerns:\n"
    "- Any vulnerabilities found, or 'None identified'\n\n"
    "Overall Score: X/10\n\n"
    "Rules: Be concise and specific. Focus on bugs, security, performance, "
    "code quality. No generic praise."
)

_client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)


async def review_diff(diff: str) -> str:
    """Send a PR diff to Claude for code review.

    Args:
        diff: The unified diff string of the pull request.

    Returns:
        The structured review text produced by Claude.
    """
    user_message = f"Please review the following pull request diff:\n\n```diff\n{diff}\n```"

    logger.info("Sending diff to Claude (%d chars)", len(diff))

    message = await _client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    review_text = next(
        (block.text for block in message.content if block.type == "text"),
        "",
    )

    logger.info(
        "Received review from Claude (stop_reason=%s, output_tokens=%d)",
        message.stop_reason,
        message.usage.output_tokens,
    )
    return review_text
