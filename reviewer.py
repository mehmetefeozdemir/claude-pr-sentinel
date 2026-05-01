import logging
from typing import Any

from claude_client import review_diff
from github_client import fetch_pr_diff, post_pr_comment

logger = logging.getLogger(__name__)

HANDLED_ACTIONS = {"opened", "synchronize", "reopened"}


async def handle_pull_request_event(payload: dict[str, Any]) -> None:
    """Orchestrate a full PR review cycle from a webhook payload.

    Args:
        payload: Parsed JSON payload from the GitHub webhook.
    """
    action: str = payload.get("action", "")
    if action not in HANDLED_ACTIONS:
        logger.debug("Ignoring PR action '%s'", action)
        return

    pull_request = payload["pull_request"]
    pull_number: int = pull_request["number"]
    repo_info = payload["repository"]
    owner: str = repo_info["owner"]["login"]
    repo: str = repo_info["name"]
    pr_title: str = pull_request.get("title", "")

    logger.info("Reviewing PR #%d '%s' in %s/%s (action=%s)", pull_number, pr_title, owner, repo, action)

    diff = await fetch_pr_diff(owner, repo, pull_number)
    if not diff:
        logger.warning("Empty diff for %s/%s#%d — skipping review", owner, repo, pull_number)
        return

    review = await review_diff(diff)
    comment = _format_comment(review, pr_title, pull_number)
    await post_pr_comment(owner, repo, pull_number, comment)


def _format_comment(review: str, pr_title: str, pull_number: int) -> str:
    """Wrap the raw review text in a formatted Markdown comment.

    Args:
        review: The raw review text from Claude.
        pr_title: The pull request title.
        pull_number: The pull request number.

    Returns:
        A formatted Markdown string ready to post as a GitHub comment.
    """
    return (
        f"## 🤖 Claude PR Sentinel Review — #{pull_number}: {pr_title}\n\n"
        f"{review}\n\n"
        f"---\n"
        f"*Automated review by [claude-pr-sentinel](https://github.com/anthropics/claude-pr-sentinel)*"
    )
