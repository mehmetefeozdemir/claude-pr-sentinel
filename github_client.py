import logging
from typing import Optional

import httpx

from config import config

logger = logging.getLogger(__name__)


async def fetch_pr_diff(owner: str, repo: str, pull_number: int) -> Optional[str]:
    """Fetch the unified diff for a pull request via the GitHub API.

    Args:
        owner: Repository owner (user or organization).
        repo: Repository name.
        pull_number: Pull request number.

    Returns:
        The raw diff string, or None on failure.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
    headers = {
        "Authorization": f"token {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        diff = response.text

    logger.info("Fetched diff for %s/%s#%d (%d chars)", owner, repo, pull_number, len(diff))
    return diff


async def post_pr_comment(owner: str, repo: str, pull_number: int, body: str) -> None:
    """Post a comment on a pull request.

    Args:
        owner: Repository owner.
        repo: Repository name.
        pull_number: Pull request number.
        body: Comment body (Markdown).
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pull_number}/comments"
    headers = {
        "Authorization": f"token {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json={"body": body})
        response.raise_for_status()

    logger.info("Posted review comment on %s/%s#%d", owner, repo, pull_number)
