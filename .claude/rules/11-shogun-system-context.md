# System Context & Engineering Standards

## 1. The "Two-Plane" Architecture
We strictly separate **Development** from **Execution**.

| Plane | Hostname | OS | Role | Allowed Actions |
| :--- | :--- | :--- | :--- | :--- |
| **Control Plane** | `ibbytech-laptop` | **Windows 11** | **Source of Truth** | Coding, Git Operations, PowerShell, SSH Initiation. **NO Production Workloads.** |
| **Execution Plane** | `*.ibbytech.com` | **Debian Linux** | **Runtime Target** | Docker Containers, Database Hosting, Python Automation. **NO Code Editing.** |

## 2. Infrastructure Topology (The Map)
*Ref: INFRASTRUCTURE_BUNDLE_v1_2*

| Node | Alias | IP | Role |
| :--- | :--- | :--- | :--- |
| **svcnode-01** | `svcnode-01.ibbytech.com` | `192.168.71.220` | **Docker Platform** (Gateways, Traefik). NO DB Data. |
| **dbnode-01** | `dbnode-01.ibbytech.com` | `192.168.71.221` | **Database** (Postgres `shogun_v1`). NO Docker. |
| **brainnode-01** | `brainnode-01.ibbytech.com` | `192.168.71.222` | **Shogun Application Tier** (Docker: shogun-core :8082, shogun-web-api :8090, shogun-web-ui :3010, cloudflared). |

## 3. The Development Workflow (Railroad Tracks)
1.  **Local Dev (Windows):** Workspace `C:\git\work\<project name>\`. Commit to `feature/<name>`.
2.  **Transport (Git):** Push to GitHub. NEVER use SCP/SFTP.
3.  **Remote Exec (Linux):** SSH to target -> `git pull` -> `docker compose up`.

## 4. Identity & Access (The Keys)
*Ref: SSH_IDENTITY_MODEL_CANONICAL*

You must explicitly "assume a persona" before any remote action.

| Persona | User Account | Identity File (ED25519) | Authorized Target | Scope |
| :--- | :--- | :--- | :--- | :--- |
| **DevOps** | `devops-agent` | `~/.ssh/devops-agent_ed25519_clean` | `svcnode-01`, `brainnode-01` | Docker lifecycle, CI/CD. |
| **DBA** | `dba-agent` | `~/.ssh/dba-agent_ed25519` | `dbnode-01` | Schema migrations, SQL. |


## 5. Network Constraints
* **Internal Only:** All nodes are on `192.168.71.x`.
* **DNS:** Do not assume internal DNS works for everything. Use IPs if aliases fail.
* **Database:** `svcnode-01` connects to `dbnode-01` via internal IP. It does not store data locally.
