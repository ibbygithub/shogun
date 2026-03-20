---
name: github-access
description: Access GitHub repositories programmatically using gh CLI or REST API. Use this skill when needing to interact with GitHub issues, pull requests, workflows, discussions, or actions. The skill automatically adapts based on available tools (gh CLI or curl) and requires GH_TOKEN for authentication.
user-invocable: true
---

# GitHub Access

## Overview

This skill enables programmatic access to GitHub repositories through either the `gh` CLI tool or the REST API with `curl`. Use this skill to interact with GitHub issues, pull requests, workflows, discussions, and GitHub Actions. The skill provides comprehensive commands and patterns for common GitHub operations.

## Prerequisites and Tool Selection

Before performing any GitHub operations, follow this workflow:

### 1. Check for GH_TOKEN

**CRITICAL**: Always verify that the `GH_TOKEN` environment variable is set before attempting any GitHub operations:

```bash
echo $GH_TOKEN
```

**If `GH_TOKEN` is not set:**
- Abort the operation immediately
- Inform the user that a GitHub token is required
- Instruct them to set `GH_TOKEN` with a valid GitHub personal access token

### 2. Check for gh CLI Availability

If `GH_TOKEN` is set, check if the `gh` CLI tool is available:

```bash
which gh
```

### 3. Load the Appropriate Reference

Based on availability, load the corresponding reference document:

- **If `gh` is available**: Read and use `references/gh-commands.md` for command examples
- **If `gh` is NOT available**: Read and use `references/curl-api.md` for REST API calls with curl

The `references/mcp-tools.md` file provides a comprehensive list of all available GitHub MCP tools and their parameters for reference.

## Key Operations

### 1. Read Issue Content
```bash
gh issue view ISSUE_NUMBER --repo OWNER/REPO
gh issue view ISSUE_NUMBER --json title,body,state,labels --repo OWNER/REPO
```

### 2. Read Pull Request Comments
```bash
gh pr view PR_NUMBER --comments --repo OWNER/REPO
gh pr view PR_NUMBER --json comments,reviews --repo OWNER/REPO
```

### 3. Check Workflow Status and Fetch Failure Logs
```bash
gh pr checks PR_NUMBER --repo OWNER/REPO
```

### 4. Search Issues
```bash
gh issue list --search "QUERY" --repo OWNER/REPO
```

### 5. Search Pull Requests
```bash
gh pr list --search "QUERY" --repo OWNER/REPO
```

## Resources

This skill includes reference documents with comprehensive command examples:

- `references/gh-commands.md` — gh CLI commands
- `references/curl-api.md` — REST API calls with curl
- `references/mcp-tools.md` — GitHub MCP tools reference
- `references/troubleshooting.md` — Common issues and fixes
