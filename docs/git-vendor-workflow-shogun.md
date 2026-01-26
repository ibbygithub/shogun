# Git Vendor Workflow Cheat Sheet (for Project Shogun)

## Purpose
A durable reference for managing fast‑moving external GitHub repositories (vendor repos),
keeping them updated efficiently, and syncing curated artifacts into the Shogun agent library
— without copy/paste chaos.

---

## Standard Directory Layout (Windows)

```
C:\git\
  vendor\    # External repos you pull/update (read‑only mindset)
  work\      # Your active development repos (Shogun, experiments)
  archive\   # Old / paused / failed experiments
```

Recommended deployment / library target:
```
C:\IbbyTech\agent-library\vendor\
```

---

## One‑Time Setup: Clone a Vendor Repo

From the vendor root:

```powershell
cd C:\git\vendor

git clone https://github.com/sickn33/antigravity-awesome-skills.git
cd antigravity-awesome-skills

git status
git log --oneline --max-count=5
git remote -v
```

This uses HTTPS + Personal Access Token (PAT).  
When prompted:
- Username → your GitHub username
- Password → your PAT (not your GitHub password)

---

## Daily Update (Minimal Download)

```powershell
git pull
```

Git downloads only new/changed objects.

---

## Inspect Changes Before Updating

```powershell
git fetch

git log --oneline --decorate HEAD..origin/main
git diff --name-status HEAD..origin/main

# Apply updates
git pull
```

### Only changes under `skills/`
```powershell
git fetch
git diff --name-only HEAD..origin/main -- skills\*
```

### Only newly added skill files
```powershell
git fetch
git diff --name-status HEAD..origin/main -- skills\* | findstr "^A"
```

---

## Sync Vendor Skills into Shogun Agent Library

Mirror only the `skills/` directory (no manual copy/paste).

```powershell
$src = "C:\git\vendor\antigravity-awesome-skills\skills"
$dst = "C:\IbbyTech\agent-library\vendor\antigravity-awesome-skills\skills"

New-Item -ItemType Directory -Force -Path $dst | Out-Null

# Option A: mirror everything under skills/
robocopy $src $dst /MIR /R:2 /W:1

# Option B: only Markdown + JSON
# robocopy $src $dst *.md *.json /E /R:2 /W:1
```

Notes:
- `/MIR` keeps destination exactly in sync (adds, updates, removes).
- Use Option B if you want a filtered library.

---

## Safety Rail (Optional)
Disable accidental pushes on vendor repos you don’t own:

```powershell
git remote set-url --push origin DISABLED
```

---

## Quick Diagnostics

```powershell
git status
git remote -v
```

---

## Shogun Usage Model

- Vendor repos = **inputs** (update via `git pull`)
- Agent library = **curated deployment output** (sync via `robocopy`)
- Never edit vendor repos directly
- Optionally record commit hashes later for reproducible builds

---

## End
This file is intended to live in:
```
C:\git\work\shogun\docs\git-vendor-workflow.md
```
or any Shogun documentation folder.
