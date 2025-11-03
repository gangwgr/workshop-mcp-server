"""Line-by-Line Code Reviewer tool for the MCP Server.

This tool provides comprehensive line-by-line code review with inline comments,
suggestions, and improvement recommendations for any code file.
"""

import os
import re
from typing import Any, Dict, List, Optional

from workshop_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()


def review_code_line_by_line(
    code_content: str,
    file_path: Optional[str] = None,
    language: Optional[str] = None,
    review_focus: Optional[List[str]] = None,
    severity_threshold: str = "info",
    is_pr_diff: bool = False,
    previous_issues: Optional[str] = None,
) -> Dict[str, Any]:
    """Review code line-by-line and provide inline comments with improvement suggestions.

    TOOL_NAME=review_code_line_by_line
    DISPLAY_NAME=Line-by-Line Code Reviewer
    USECASE=Comprehensive code review with inline comments on each line needing improvement
    INSTRUCTIONS=1. Provide code content or file path, 2. Optionally specify language and review focus, 3. Receive detailed line-by-line review with inline comments
    INPUT_DESCRIPTION=code_content (str): Code to review, file_path (str, optional): Path to code file, language (str, optional): Programming language, review_focus (list, optional): Focus areas (security, performance, style, bugs, best-practices), severity_threshold (str): Minimum severity to report (info, warning, error, critical)
    OUTPUT_DESCRIPTION=Dictionary with line-by-line review results, inline comments, improvement suggestions, and summary statistics
    EXAMPLES=review_code_line_by_line(code_content), review_code_line_by_line(file_path="/path/to/file.py", review_focus=["security", "performance"])
    PREREQUISITES=None
    RELATED_TOOLS=review_pull_request_comprehensive, quick_code_check

    This tool provides:
    - Line-by-line analysis with inline comments
    - Issue severity classification (info, warning, error, critical)
    - Improvement suggestions for each issue
    - Code smells and anti-pattern detection
    - Security vulnerability identification
    - Performance optimization suggestions
    - Best practice recommendations
    - Refactoring suggestions

    Args:
        code_content: Code to review (required if file_path not provided)
        file_path: Path to code file (optional, used if code_content not provided)
        language: Programming language (auto-detected if not provided)
        review_focus: List of focus areas (default: all)
        severity_threshold: Minimum severity to report (default: "info")

    Returns:
        Dictionary containing detailed line-by-line review with inline comments

    Raises:
        ValueError: If neither code_content nor file_path is provided
    """
    try:
        # Load code from file if file_path provided
        if file_path and not code_content:
            if not os.path.exists(file_path):
                raise ValueError(f"File not found: {file_path}")

            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()

            # Auto-detect language from file extension
            if not language:
                language = _detect_language_from_path(file_path)

        if not code_content:
            raise ValueError("Either code_content or file_path must be provided")

        # Try LLM-powered review first
        try:
            from workshop_mcp_server.src.tools.llm_provider import review_code, is_available, get_mode, get_model
            if is_available():
                llm_result = review_code(
                    code_content,
                    language=language or "unknown",
                    focus=review_focus,
                    is_pr_diff=is_pr_diff,
                    previous_issues=previous_issues
                )
                if llm_result:
                    current_mode = get_mode()
                    current_model = get_model()
                    mode_label = f"{current_mode} ({current_model})"
                    logger.info(f"LLM-powered code review completed successfully via {mode_label}")
                    return {
                        "status": "success",
                        "file_path": file_path or "inline_code",
                        "language": language or "auto-detected",
                        "mode": "llm",
                        "llm_provider": current_mode,
                        "llm_model": current_model,
                        "llm_review": llm_result,
                        "message": f"AI-powered code review completed ({mode_label})",
                    }
        except Exception as llm_err:
            logger.warning(f"LLM review unavailable, falling back to pattern-based: {llm_err}")

        logger.info(f"Starting line-by-line code review (language: {language or 'auto-detect'})")

        # Auto-detect language if not provided
        if not language:
            language = _detect_language_from_content(code_content)

        # Set default review focus
        if not review_focus:
            review_focus = ["security", "performance", "style", "bugs", "best-practices", "maintainability"]

        # Split code into lines
        lines = code_content.split('\n')

        # Initialize review results
        review_results = {
            "status": "success",
            "file_path": file_path or "inline_code",
            "language": language,
            "total_lines": len(lines),
            "review_focus": review_focus,
            "severity_threshold": severity_threshold,
            "line_reviews": [],
            "issues_by_severity": {
                "critical": 0,
                "error": 0,
                "warning": 0,
                "info": 0,
            },
            "issues_by_category": {
                "security": 0,
                "performance": 0,
                "style": 0,
                "bugs": 0,
                "best-practices": 0,
                "maintainability": 0,
            },
            "total_issues": 0,
        }

        # Review each line
        for line_number, line in enumerate(lines, 1):
            line_review = _review_single_line(
                line_number=line_number,
                line_content=line,
                language=language,
                review_focus=review_focus,
                severity_threshold=severity_threshold,
                all_lines=lines,
            )

            if line_review["issues"]:
                review_results["line_reviews"].append(line_review)

                # Count issues by severity and category
                for issue in line_review["issues"]:
                    review_results["issues_by_severity"][issue["severity"]] += 1
                    review_results["issues_by_category"][issue["category"]] += 1
                    review_results["total_issues"] += 1

        # Generate summary
        review_results["summary"] = _generate_review_summary(review_results)

        # Generate recommendations
        review_results["recommendations"] = _generate_recommendations(review_results, language)

        logger.info(f"Line-by-line review completed. Found {review_results['total_issues']} issues")
        return review_results

    except Exception as e:
        logger.error(f"Error during line-by-line code review: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to perform line-by-line code review",
        }


def _review_single_line(
    line_number: int,
    line_content: str,
    language: str,
    review_focus: List[str],
    severity_threshold: str,
    all_lines: List[str],
) -> Dict[str, Any]:
    """Review a single line of code."""
    line_review = {
        "line_number": line_number,
        "line_content": line_content,
        "issues": [],
    }

    # Skip empty lines and comments for some checks
    stripped_line = line_content.strip()
    if not stripped_line:
        return line_review

    # Run all applicable checks
    issues = []

    if "security" in review_focus:
        issues.extend(_check_security_issues(line_number, line_content, language))

    if "performance" in review_focus:
        issues.extend(_check_performance_issues(line_number, line_content, language, all_lines))

    if "style" in review_focus:
        issues.extend(_check_style_issues(line_number, line_content, language))

    if "bugs" in review_focus:
        issues.extend(_check_potential_bugs(line_number, line_content, language, all_lines))

    if "best-practices" in review_focus:
        issues.extend(_check_best_practices(line_number, line_content, language, all_lines))

    if "maintainability" in review_focus:
        issues.extend(_check_maintainability(line_number, line_content, language))

    # Filter by severity threshold
    severity_levels = {"info": 0, "warning": 1, "error": 2, "critical": 3}
    threshold_level = severity_levels.get(severity_threshold, 0)

    filtered_issues = [
        issue for issue in issues
        if severity_levels.get(issue["severity"], 0) >= threshold_level
    ]

    line_review["issues"] = filtered_issues
    return line_review


def _check_security_issues(line_number: int, line: str, language: str) -> List[Dict[str, Any]]:
    """Check for security issues."""
    issues = []

    # Common security patterns
    security_patterns = {
        "hardcoded_secret": {
            "patterns": [
                r'password\s*=\s*["\'][\w]+["\']',
                r'api[_-]?key\s*=\s*["\'][\w]+["\']',
                r'secret\s*=\s*["\'][\w]+["\']',
                r'token\s*=\s*["\'][\w]+["\']',
            ],
            "severity": "critical",
            "message": "Potential hardcoded secret/password detected",
            "suggestion": "Use environment variables or secret management service",
        },
        "sql_injection": {
            "patterns": [
                r'execute\(["\'].*%s.*["\']\s*%',
                r'execute\(["\'].*\+.*["\']\)',
                r'\.query\(["\'].*\+.*["\']\)',
            ],
            "severity": "critical",
            "message": "Potential SQL injection vulnerability",
            "suggestion": "Use parameterized queries or prepared statements",
        },
        "command_injection": {
            "patterns": [
                r'os\.system\(',
                r'subprocess\.call\(.*shell\s*=\s*True',
                r'exec\(',
                r'eval\(',
            ],
            "severity": "error",
            "message": "Potential command injection vulnerability",
            "suggestion": "Avoid shell=True, use subprocess with argument lists, avoid eval/exec",
        },
        "insecure_random": {
            "patterns": [
                r'random\.random\(',
                r'random\.choice\(',
                r'Math\.random\(',
            ],
            "severity": "warning",
            "message": "Using insecure random number generator for security-sensitive operation",
            "suggestion": "Use secrets module (Python) or crypto.randomBytes (Node.js) for security",
        },
    }

    for check_name, check_data in security_patterns.items():
        for pattern in check_data["patterns"]:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append({
                    "category": "security",
                    "severity": check_data["severity"],
                    "message": check_data["message"],
                    "suggestion": check_data["suggestion"],
                    "line_number": line_number,
                })
                break

    return issues


def _check_performance_issues(line_number: int, line: str, language: str, all_lines: List[str]) -> List[Dict[str, Any]]:
    """Check for performance issues."""
    issues = []

    if language == "python":
        # Inefficient string concatenation in loop
        if re.search(r'for .* in .*:', line):
            # Check next few lines for string concatenation
            for i in range(line_number, min(line_number + 5, len(all_lines))):
                if i < len(all_lines) and re.search(r'\w+\s*\+=\s*["\']', all_lines[i]):
                    issues.append({
                        "category": "performance",
                        "severity": "warning",
                        "message": "String concatenation in loop is inefficient",
                        "suggestion": "Use list.append() and ''.join() or use io.StringIO",
                        "line_number": line_number,
                    })
                    break

        # Global lookups in loops
        if 'global ' in line.lower():
            issues.append({
                "category": "performance",
                "severity": "info",
                "message": "Global variable access can be slow",
                "suggestion": "Consider using local variables or function parameters",
                "line_number": line_number,
            })

        # Multiple list comprehensions that could be combined
        if line.count('[') > 2 and 'for ' in line:
            issues.append({
                "category": "performance",
                "severity": "info",
                "message": "Multiple list comprehensions could be optimized",
                "suggestion": "Consider combining into single comprehension or using generator",
                "line_number": line_number,
            })

    return issues


def _check_style_issues(line_number: int, line: str, language: str) -> List[Dict[str, Any]]:
    """Check for style issues."""
    issues = []

    # Line too long
    if len(line) > 120:
        issues.append({
            "category": "style",
            "severity": "info",
            "message": f"Line too long ({len(line)} > 120 characters)",
            "suggestion": "Break line into multiple lines for better readability",
            "line_number": line_number,
        })

    # Trailing whitespace
    if line.rstrip() != line.rstrip('\n').rstrip():
        issues.append({
            "category": "style",
            "severity": "info",
            "message": "Trailing whitespace detected",
            "suggestion": "Remove trailing whitespace",
            "line_number": line_number,
        })

    if language == "python":
        # PEP 8 style checks
        # Multiple statements on one line
        if ';' in line and not line.strip().startswith('#'):
            issues.append({
                "category": "style",
                "severity": "warning",
                "message": "Multiple statements on one line",
                "suggestion": "Use separate lines for each statement (PEP 8)",
                "line_number": line_number,
            })

        # Comparison to True/False
        if re.search(r'==\s*(True|False)', line) or re.search(r'(True|False)\s*==', line):
            issues.append({
                "category": "style",
                "severity": "warning",
                "message": "Comparison to True/False is not Pythonic",
                "suggestion": "Use 'if variable:' or 'if not variable:' instead",
                "line_number": line_number,
            })

    return issues


def _check_potential_bugs(line_number: int, line: str, language: str, all_lines: List[str]) -> List[Dict[str, Any]]:
    """Check for potential bugs."""
    issues = []

    if language == "python":
        # Mutable default arguments
        if re.search(r'def\s+\w+\([^)]*=\s*\[\]', line) or re.search(r'def\s+\w+\([^)]*=\s*\{\}', line):
            issues.append({
                "category": "bugs",
                "severity": "error",
                "message": "Mutable default argument (list/dict) detected",
                "suggestion": "Use None as default and initialize inside function",
                "line_number": line_number,
            })

        # Bare except clause
        if re.search(r'except\s*:', line):
            issues.append({
                "category": "bugs",
                "severity": "warning",
                "message": "Bare except clause catches all exceptions",
                "suggestion": "Specify exception type(s) to catch",
                "line_number": line_number,
            })

        # Using 'is' for comparison
        if re.search(r'is\s+["\']', line) or re.search(r'is\s+\d', line):
            issues.append({
                "category": "bugs",
                "severity": "error",
                "message": "Using 'is' for value comparison instead of identity",
                "suggestion": "Use '==' for value comparison, 'is' only for None/True/False",
                "line_number": line_number,
            })

        # Missing return in function
        if re.search(r'def\s+\w+\([^)]*\)\s*->\s*(?!None)', line):
            # Check if function has return statement in next lines
            has_return = False
            for i in range(line_number, min(line_number + 10, len(all_lines))):
                if i < len(all_lines) and 'return ' in all_lines[i]:
                    has_return = True
                    break
            if not has_return:
                issues.append({
                    "category": "bugs",
                    "severity": "warning",
                    "message": "Function has type hint but no visible return statement",
                    "suggestion": "Ensure function returns appropriate value",
                    "line_number": line_number,
                })

    elif language == "javascript":
        # Using == instead of ===
        if re.search(r'[^=!<>]==[^=]', line):
            issues.append({
                "category": "bugs",
                "severity": "warning",
                "message": "Using loose equality (==) instead of strict equality (===)",
                "suggestion": "Use === for strict equality comparison",
                "line_number": line_number,
            })

    return issues


def _check_best_practices(line_number: int, line: str, language: str, all_lines: List[str]) -> List[Dict[str, Any]]:
    """Check for best practice violations."""
    issues = []

    if language == "python":
        # TODO/FIXME comments
        if re.search(r'#\s*(TODO|FIXME|XXX|HACK)', line, re.IGNORECASE):
            issues.append({
                "category": "best-practices",
                "severity": "info",
                "message": "TODO/FIXME comment found",
                "suggestion": "Consider creating a ticket to track this work",
                "line_number": line_number,
            })

        # Print statements (should use logging)
        if re.search(r'\bprint\s*\(', line) and not line.strip().startswith('#'):
            issues.append({
                "category": "best-practices",
                "severity": "info",
                "message": "Using print() instead of logging",
                "suggestion": "Consider using logging module for production code",
                "line_number": line_number,
            })

        # Type hints missing
        if re.search(r'def\s+\w+\([^)]*\)\s*:', line) and '->' not in line:
            if 'self' in line or '__init__' in line:
                pass  # Skip methods for now
            else:
                issues.append({
                    "category": "best-practices",
                    "severity": "info",
                    "message": "Function missing type hints",
                    "suggestion": "Add type hints for better code documentation",
                    "line_number": line_number,
                })

    return issues


def _check_maintainability(line_number: int, line: str, language: str) -> List[Dict[str, Any]]:
    """Check for maintainability issues."""
    issues = []

    # Complex boolean expressions
    and_count = line.count(' and ')
    or_count = line.count(' or ')
    if and_count + or_count > 2:
        issues.append({
            "category": "maintainability",
            "severity": "warning",
            "message": "Complex boolean expression",
            "suggestion": "Consider breaking into multiple conditions or using a helper function",
            "line_number": line_number,
        })

    # Nested ternary operators
    if language in ["python", "javascript"]:
        ternary_count = line.count('if') + line.count('else') if language == "python" else line.count('?')
        if ternary_count > 1:
            issues.append({
                "category": "maintainability",
                "severity": "warning",
                "message": "Nested ternary/conditional operators",
                "suggestion": "Use if-else statements for better readability",
                "line_number": line_number,
            })

    # Magic numbers
    numbers = re.findall(r'\b(\d{2,})\b', line)
    if numbers and not line.strip().startswith('#'):
        # Exclude common values
        magic_numbers = [n for n in numbers if n not in ['10', '100', '1000', '60', '24']]
        if magic_numbers:
            issues.append({
                "category": "maintainability",
                "severity": "info",
                "message": f"Magic number(s) found: {', '.join(magic_numbers)}",
                "suggestion": "Consider using named constants",
                "line_number": line_number,
            })

    return issues


def _detect_language_from_path(file_path: str) -> str:
    """Detect programming language from file extension."""
    extension_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.go': 'go',
        '.rb': 'ruby',
        '.php': 'php',
        '.c': 'c',
        '.cpp': 'cpp',
        '.cs': 'csharp',
        '.rs': 'rust',
        '.sh': 'bash',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.json': 'json',
    }

    _, ext = os.path.splitext(file_path)
    return extension_map.get(ext.lower(), 'unknown')


def _detect_language_from_content(code_content: str) -> str:
    """Detect programming language from code content."""
    # Simple heuristics
    if 'def ' in code_content and 'import ' in code_content:
        return 'python'
    elif 'function ' in code_content and ('var ' in code_content or 'let ' in code_content):
        return 'javascript'
    elif 'public class ' in code_content or 'public static void' in code_content:
        return 'java'
    elif 'func ' in code_content and 'package ' in code_content:
        return 'go'
    else:
        return 'unknown'


def _generate_review_summary(review_results: Dict[str, Any]) -> str:
    """Generate human-readable review summary."""
    total_issues = review_results["total_issues"]
    total_lines = review_results["total_lines"]
    issues_by_severity = review_results["issues_by_severity"]

    summary = f"""
Code Review Summary
{'=' * 80}
File: {review_results['file_path']}
Language: {review_results['language']}
Total Lines: {total_lines}
Lines with Issues: {len(review_results['line_reviews'])}

Issues Found: {total_issues}
  Critical: {issues_by_severity['critical']} 🔴
  Errors:   {issues_by_severity['error']} 🟠
  Warnings: {issues_by_severity['warning']} 🟡
  Info:     {issues_by_severity['info']} 🔵

Issues by Category:
"""

    for category, count in review_results["issues_by_category"].items():
        if count > 0:
            summary += f"  {category.title()}: {count}\n"

    summary += f"\n{'=' * 80}"

    return summary.strip()


def _generate_recommendations(review_results: Dict[str, Any], language: str) -> List[str]:
    """Generate overall recommendations based on review results."""
    recommendations = []
    issues_by_severity = review_results["issues_by_severity"]
    issues_by_category = review_results["issues_by_category"]

    # Critical issues
    if issues_by_severity["critical"] > 0:
        recommendations.append(
            f"⚠️ URGENT: Fix {issues_by_severity['critical']} critical security issue(s) immediately"
        )

    # Security
    if issues_by_category["security"] > 0:
        recommendations.append(
            f"🔒 Review and address {issues_by_category['security']} security issue(s)"
        )

    # Bugs
    if issues_by_category["bugs"] > 0:
        recommendations.append(
            f"🐛 Fix {issues_by_category['bugs']} potential bug(s) before deployment"
        )

    # Performance
    if issues_by_category["performance"] > 5:
        recommendations.append(
            "⚡ Consider performance optimizations - multiple issues detected"
        )

    # Style
    if issues_by_category["style"] > 10:
        recommendations.append(
            f"📝 Run code formatter to fix {issues_by_category['style']} style issue(s)"
        )

    # General
    if review_results["total_issues"] == 0:
        recommendations.append("✅ Code looks good! No major issues detected.")
    elif review_results["total_issues"] > 20:
        recommendations.append(
            "🔧 Consider refactoring - code has many issues that affect quality"
        )

    return recommendations
