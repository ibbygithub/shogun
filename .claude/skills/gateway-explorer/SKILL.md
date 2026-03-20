---
name: gateway-explorer
description: Use this skill when you need to interact with internal ibbytech.com API gateways, including Google Places, Telegram, LLM, Tavily, and Scraper services. Knows endpoint discovery, auth patterns, and connectivity rules.
user-invocable: true
---

## Goal
Provide a secure, standardized way to discover and authenticate with internal API resources without hardcoding keys in the context.

## Instructions
1.  **Identify Resource:** Check `.claude/assets/gateway-map.json` to find the correct `endpoint` for the requested service.
2.  **Auth Protocol:** Never ask the user for a key. Run `scripts/get-credential.sh <service_name>` to retrieve the token into a temporary environment variable.
3.  **Connectivity:** All requests must originate from `brainnode-01` or `svcnode-01` per the System Context.

## Constraints
* DO NOT print API keys to the console/chat.
* DO NOT commit keys to Git.
* DO NOT use external DNS if internal resolution fails; fallback to IP `192.168.71.220`.
