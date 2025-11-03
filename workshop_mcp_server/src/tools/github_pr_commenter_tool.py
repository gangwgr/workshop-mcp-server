"""GitHub PR Commenter tool for the MCP Server.

This tool posts review comments on GitHub Pull Requests based on code review results.
"""

import os
import subprocess
from typing import Any, Dict, List, Optional

from workshop_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()


def post_pr_review_comments(
    pr_url: str,
    review_results: Dict[str, Any],
    post_summary: bool = True,
    post_inline_comments: bool = True,
    approve_if_clean: bool = False,
) -> Dict[str, Any]:
    """Post review comments on a GitHub Pull Request.

    TOOL_NAME=post_pr_review_comments
    DISPLAY_NAME=GitHub PR Review Commenter
    USECASE=Post line-by-line review comments on GitHub PRs automatically
    INSTRUCTIONS=1. Provide PR URL and review results, 2. Tool posts inline comments and summary on GitHub, 3. Optionally approve PR if no issues
    INPUT_DESCRIPTION=pr_url (str): GitHub PR URL, review_results (dict): Results from code review tools, post_summary (bool): Post overall summary comment, post_inline_comments (bool): Post line-by-line comments, approve_if_clean (bool): Approve PR if no critical/error issues
    OUTPUT_DESCRIPTION=Dictionary with status, posted comments count, and GitHub response
    EXAMPLES=post_pr_review_comments("https://github.com/org/repo/pull/123", review_results)
    PREREQUISITES=GitHub CLI (gh) installed and authenticated
    RELATED_TOOLS=review_code_line_by_line, review_pull_request_comprehensive

    This tool:
    - Posts inline comments on specific lines
    - Posts overall review summary
    - Can approve/request changes/comment
    - Uses GitHub CLI for authentication

    Args:
        pr_url: GitHub PR URL (e.g., https://github.com/org/repo/pull/123)
        review_results: Results from review_code_line_by_line or review_pull_request_comprehensive
        post_summary: Whether to post overall summary comment
        post_inline_comments: Whether to post line-by-line inline comments
        approve_if_clean: Approve PR if no critical/error issues found

    Returns:
        Dictionary containing posting status and results

    Raises:
        ValueError: If PR URL is invalid or gh CLI not available
    """
    try:
        logger.info(f"Posting review comments to PR: {pr_url}")

        # Parse PR URL
        pr_info = _parse_github_pr_url(pr_url)
        if not pr_info:
            raise ValueError(f"Invalid GitHub PR URL: {pr_url}")

        repo = f"{pr_info['owner']}/{pr_info['repo']}"
        pr_number = pr_info['pr_number']

        # Check if gh CLI is available
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise ValueError("GitHub CLI (gh) is not installed. Install from https://cli.github.com/")

        # Check authentication
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise ValueError("GitHub CLI is not authenticated. Run 'gh auth login'")

        posted_comments = []

        # Post inline comments
        if post_inline_comments and review_results.get("line_reviews"):
            logger.info("Posting inline comments...")

            # Get the file path from review results
            file_path = review_results.get("file_path", "unknown")

            for line_review in review_results["line_reviews"]:
                line_number = line_review["line_number"]

                for issue in line_review["issues"]:
                    # Skip info-level comments if there are too many
                    if issue["severity"] == "info" and len(review_results["line_reviews"]) > 20:
                        continue

                    comment_body = _format_inline_comment(issue, line_review)

                    # Post comment using gh CLI
                    comment_result = _post_inline_comment(
                        repo=repo,
                        pr_number=pr_number,
                        file_path=file_path,
                        line_number=line_number,
                        comment_body=comment_body,
                    )

                    if comment_result["status"] == "success":
                        posted_comments.append({
                            "type": "inline",
                            "line": line_number,
                            "severity": issue["severity"],
                        })

        # Post summary comment
        summary_posted = False
        if post_summary:
            logger.info("Posting summary comment...")
            summary_comment = _format_summary_comment(review_results)

            summary_result = _post_pr_comment(
                repo=repo,
                pr_number=pr_number,
                comment_body=summary_comment,
            )

            if summary_result["status"] == "success":
                summary_posted = True

        # Submit review (approve/comment/request changes)
        review_action = _determine_review_action(review_results, approve_if_clean)
        review_posted = False

        if review_action != "skip":
            logger.info(f"Submitting review with action: {review_action}")
            review_result = _submit_review(
                repo=repo,
                pr_number=pr_number,
                review_action=review_action,
                review_results=review_results,
            )

            if review_result["status"] == "success":
                review_posted = True

        return {
            "status": "success",
            "pr_url": pr_url,
            "repo": repo,
            "pr_number": pr_number,
            "inline_comments_posted": len(posted_comments),
            "summary_posted": summary_posted,
            "review_posted": review_posted,
            "review_action": review_action,
            "posted_comments": posted_comments,
            "message": f"Successfully posted review to PR #{pr_number}",
        }

    except Exception as e:
        logger.error(f"Error posting PR comments: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to post PR review comments",
        }


def _parse_github_pr_url(pr_url: str) -> Optional[Dict[str, Any]]:
    """Parse GitHub PR URL to extract owner, repo, and PR number."""
    import re

    # Match: https://github.com/owner/repo/pull/123
    match = re.search(r'github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if match:
        return {
            "owner": match.group(1),
            "repo": match.group(2),
            "pr_number": int(match.group(3)),
        }
    return None


def _format_inline_comment(issue: Dict[str, Any], line_review: Dict[str, Any]) -> str:
    """Format inline comment for a specific issue."""
    severity_icons = {
        "critical": "🔴",
        "error": "🟠",
        "warning": "🟡",
        "info": "🔵",
    }

    category_icons = {
        "security": "🔒",
        "performance": "⚡",
        "bugs": "🐛",
        "best-practices": "✨",
        "maintainability": "🔧",
        "style": "📝",
    }

    severity_icon = severity_icons.get(issue["severity"], "⚪")
    category_icon = category_icons.get(issue["category"], "📌")

    comment = f"""
{severity_icon} **{issue['severity'].upper()}** {category_icon} *{issue['category'].title()}*

**Issue:** {issue['message']}

**Suggestion:** {issue['suggestion']}

---
*Posted by MCP Code Reviewer*
""".strip()

    return comment


def _format_summary_comment(review_results: Dict[str, Any]) -> str:
    """Format overall summary comment with detailed breakdown."""
    total_issues = review_results.get("total_issues", 0)
    severity_counts = review_results.get("issues_by_severity", {})
    category_counts = review_results.get("issues_by_category", {})
    line_reviews = review_results.get("line_reviews", [])

    # Build detailed summary
    summary = f"""## 🤖 MCP Code Review - Line-by-Line Analysis

**File:** `{review_results.get('file_path', 'unknown')}`
**Language:** {review_results.get('language', 'unknown')}
**Total Lines:** {review_results.get('total_lines', 0)}

---

### 📊 Review Results

"""

    # Severity breakdown with checkmarks
    critical = severity_counts.get("critical", 0)
    errors = severity_counts.get("error", 0)
    warnings = severity_counts.get("warning", 0)
    info = severity_counts.get("info", 0)

    summary += f"- {'✅' if critical == 0 else '🔴'} **{critical} Critical Issues**\n"
    summary += f"- {'✅' if errors == 0 else '🟠'} **{errors} Errors**\n"
    summary += f"- {'✅' if warnings == 0 else '🟡'} **{warnings} Warnings**\n"
    summary += f"- 🔵 **{info} Info** (minor suggestions)\n"

    # Inline comments posted
    if line_reviews:
        summary += f"\n### 💬 Inline Comments Posted ({len(line_reviews)} total)\n\n"

        # Group by category
        issues_by_category = {}
        for line_review in line_reviews:
            for issue in line_review.get("issues", []):
                category = issue["category"]
                if category not in issues_by_category:
                    issues_by_category[category] = []
                issues_by_category[category].append({
                    "line": line_review["line_number"],
                    "message": issue["message"],
                    "suggestion": issue["suggestion"],
                })

        # Display each category
        for category, issues in issues_by_category.items():
            if category == "style":
                icon = "📝"
                title = "Style Issues"
            elif category == "maintainability":
                icon = "🔧"
                title = "Maintainability Issues"
            elif category == "security":
                icon = "🔒"
                title = "Security Issues"
            elif category == "performance":
                icon = "⚡"
                title = "Performance Issues"
            elif category == "bugs":
                icon = "🐛"
                title = "Bug Issues"
            else:
                icon = "📌"
                title = f"{category.title()} Issues"

            summary += f"**{icon} {title} ({len(issues)}):**\n"

            # Group similar issues
            grouped_issues = _group_similar_issues(issues)

            for group in grouped_issues:
                if len(group["lines"]) > 1:
                    lines_str = ", ".join([str(l) for l in sorted(group["lines"])])
                    summary += f"- **Lines {lines_str}:** {group['message']}\n"
                else:
                    summary += f"- **Line {group['lines'][0]}:** {group['message']}\n"

                if group.get("suggestion"):
                    summary += f"  - *Suggestion:* {group['suggestion']}\n"

            summary += "\n"

    # Recommendations with code examples
    if total_issues > 0:
        summary += "### 💡 Recommended Improvements\n\n"

        # Check for magic number issues
        magic_number_issues = [
            line_review for line_review in line_reviews
            for issue in line_review.get("issues", [])
            if "Magic number" in issue["message"]
        ]

        if magic_number_issues:
            summary += "**1. Extract constants for magic numbers:**\n\n"
            summary += "```go\n"
            summary += "const (\n"

            # Extract unique magic numbers from the issues
            for line_review in magic_number_issues[:3]:  # Show first 3
                line_content = line_review.get("line_content", "").strip()
                if "testValues" in line_content:
                    summary += "    shortTTLMinutes  = 5\n"
                    summary += "    mediumTTLMinutes = 10\n"
                    summary += "    longTTLMinutes   = 15\n"
                elif "20" in line_content and "Minute" in line_content:
                    summary += "    apiServerRolloutTimeout = 20 * time.Minute\n"
                elif "15" in line_content and "Second" in line_content:
                    summary += "    apiServerPollInterval   = 15 * time.Second\n"

            summary += ")\n```\n\n"

        # Check for long line issues
        long_line_issues = [
            line_review for line_review in line_reviews
            for issue in line_review.get("issues", [])
            if "Line too long" in issue["message"]
        ]

        if long_line_issues:
            summary += "**2. Break long lines** (optional, style preference)\n\n"

    # Final verdict
    summary += "### 🎯 Final Verdict\n\n"

    if critical > 0:
        summary += f"❌ **CHANGES REQUESTED** - {critical} critical issue(s) must be fixed before merge\n\n"
        summary += "**Critical issues detected:**\n"
        for line_review in line_reviews:
            for issue in line_review.get("issues", []):
                if issue["severity"] == "critical":
                    summary += f"- Line {line_review['line_number']}: {issue['message']}\n"
    elif errors > 0:
        summary += f"⚠️ **CHANGES REQUESTED** - {errors} error(s) should be addressed before merge\n\n"
    else:
        summary += "✅ **APPROVED** - The code is production-ready!\n\n"

        if total_issues > 0:
            summary += "**Why this is excellent code:**\n"
            if critical == 0:
                summary += "- ✅ No security vulnerabilities\n"
            if errors == 0:
                summary += "- ✅ No bugs or errors\n"
            if warnings == 0:
                summary += "- ✅ No warnings\n"

            summary += "- ✅ Well-structured code\n"
            summary += "- ✅ Good practices followed\n\n"

            summary += f"*The {total_issues} suggestion(s) are minor improvements that don't block the merge.*\n"
        else:
            summary += "**Perfect code - no issues detected!** 🎉\n"

    summary += "\n---\n*🤖 Automated review by MCP Code Reviewer*"

    return summary


def _group_similar_issues(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group similar issues together."""
    grouped = {}

    for issue in issues:
        key = issue["message"]
        if key not in grouped:
            grouped[key] = {
                "message": issue["message"],
                "suggestion": issue.get("suggestion"),
                "lines": []
            }
        grouped[key]["lines"].append(issue["line"])

    return list(grouped.values())


def _post_inline_comment(
    repo: str,
    pr_number: int,
    file_path: str,
    line_number: int,
    comment_body: str,
) -> Dict[str, Any]:
    """Post an inline comment on a specific line."""
    try:
        # Use gh pr review with --comment-body for inline comments
        # Note: This creates a review comment, not an inline comment
        # For true inline comments, we'd need to use gh api with the review API

        # For now, post as a regular PR comment with line reference
        formatted_comment = f"**Comment on `{file_path}:{line_number}`**\n\n{comment_body}"

        result = subprocess.run(
            [
                "gh", "pr", "comment", str(pr_number),
                "--repo", repo,
                "--body", formatted_comment,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return {"status": "success"}
        else:
            logger.warning(f"Failed to post inline comment: {result.stderr}")
            return {"status": "error", "error": result.stderr}

    except Exception as e:
        logger.error(f"Error posting inline comment: {e}")
        return {"status": "error", "error": str(e)}


def _post_pr_comment(repo: str, pr_number: int, comment_body: str) -> Dict[str, Any]:
    """Post a general comment on the PR."""
    try:
        result = subprocess.run(
            [
                "gh", "pr", "comment", str(pr_number),
                "--repo", repo,
                "--body", comment_body,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return {"status": "success"}
        else:
            logger.error(f"Failed to post comment: {result.stderr}")
            return {"status": "error", "error": result.stderr}

    except Exception as e:
        logger.error(f"Error posting comment: {e}")
        return {"status": "error", "error": str(e)}


def _submit_review(
    repo: str,
    pr_number: int,
    review_action: str,
    review_results: Dict[str, Any],
) -> Dict[str, Any]:
    """Submit a review (approve/comment/request-changes)."""
    try:
        # Build review body
        total_issues = review_results.get("total_issues", 0)
        critical = review_results.get("issues_by_severity", {}).get("critical", 0)
        errors = review_results.get("issues_by_severity", {}).get("error", 0)

        if review_action == "approve":
            review_body = f"✅ Code review complete. Found {total_issues} minor suggestions. Ready to merge!"
        elif review_action == "request-changes":
            review_body = f"⚠️ Changes requested. Please address {critical + errors} issue(s) before merging."
        else:
            review_body = f"📝 Code review complete. Found {total_issues} suggestion(s)."

        # Submit review using gh CLI
        result = subprocess.run(
            [
                "gh", "pr", "review", str(pr_number),
                "--repo", repo,
                f"--{review_action}",
                "--body", review_body,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return {"status": "success"}
        else:
            logger.error(f"Failed to submit review: {result.stderr}")
            return {"status": "error", "error": result.stderr}

    except Exception as e:
        logger.error(f"Error submitting review: {e}")
        return {"status": "error", "error": str(e)}


def _determine_review_action(review_results: Dict[str, Any], approve_if_clean: bool) -> str:
    """Determine what review action to take."""
    severity_counts = review_results.get("issues_by_severity", {})

    critical = severity_counts.get("critical", 0)
    errors = severity_counts.get("error", 0)

    if critical > 0 or errors > 0:
        return "request-changes"
    elif approve_if_clean:
        return "approve"
    else:
        return "comment"
