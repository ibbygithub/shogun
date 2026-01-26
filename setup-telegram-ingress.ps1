# setup-telegram-ingress.ps1
# Creates deterministic file scaffolding for:
# platform-services/telegram-ingress-service/{gateway,upstream-stub}
# Writes files as UTF-8 (no BOM). Does NOT run Docker or npm.

$ErrorActionPreference = "Stop"

function Find-RepoRoot {
  $here = Get-Location
  $cur = $here.Path

  for ($i = 0; $i -lt 12; $i++) {
    if (Test-Path (Join-Path $cur ".git") -PathType Container) {
      return $cur
    }
    $parent = Split-Path $cur -Parent
    if (-not $parent -or $parent -eq $cur) { break }
    $cur = $parent
  }

  throw "Could not find repo root (.git). Run this from inside the shogun repo folder."
}

function Write-TextFileNoBom([string]$Path, [string]$Content) {
  $dir = Split-Path $Path -Parent
  if ($dir -and -not (Test-Path $dir)) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
  }

  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

$repoRoot = Find-RepoRoot
Write-Host "Repo root:" $repoRoot

$svcRoot = Join-Path $repoRoot "platform-services\telegram-ingress-service"
$gatewayDir = Join-Path $svcRoot "gateway"
$stubDir    = Join-Path $svcRoot "upstream-stub"

# Ensure directories exist
New-Item -ItemType Directory -Force -Path $svcRoot, $gatewayDir, $stubDir | Out-Null

# Canonical docker-compose.yml (safe to overwrite)
$composePath = Join-Path $svcRoot "docker-compose.yml"
$compose = @"
services:
  telegram-gateway:
    build: ./gateway
    container_name: telegram-gateway
    restart: unless-stopped
    env_file:
      - .env
    depends_on:
      - upstream-stub

  upstream-stub:
    build: ./upstream-stub
    container_name: shogun-core-stub
    restart: unless-stopped
    # No ports needed; gateway talks over docker network
"@
Write-TextFileNoBom $composePath $compose

# .env (create if missing; do NOT overwrite if already present to protect secrets)
$envPath = Join-Path $svcRoot ".env"
if (-not (Test-Path $envPath)) {
  $envTemplate = @"
# Telegram bot token for this project instance
TELEGRAM_BOT_TOKEN=REPLACE_ME

# Comma-separated Telegram user IDs allowed to use the bot
ALLOWED_USER_IDS=REPLACE_ME

# Optional: comma-separated group chat IDs (leave blank for DM-only)
ALLOWED_GROUP_IDS=

# Where the gateway forwards normalized events
UPSTREAM_URL=http://upstream-stub:8080/telegram/events
UPSTREAM_TIMEOUT_MS=30000

# Transport mode
TELEGRAM_MODE=polling
"@
  Write-TextFileNoBom $envPath $envTemplate
} else {
  Write-Host "NOTE: .env already exists; leaving it unchanged to avoid overwriting secrets."
}

# --------------------
# Upstream stub
# --------------------
$stubDockerfilePath = Join-Path $stubDir "Dockerfile"
$stubPackagePath    = Join-Path $stubDir "package.json"
$stubIndexPath      = Join-Path $stubDir "index.js"

$stubDockerfile = @"
FROM node:20-slim
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --omit=dev
COPY index.js ./
EXPOSE 8080
CMD ["node", "index.js"]
"@

$stubPackage = @"
{
  "name": "shogun-core-stub",
  "version": "1.0.0",
  "dependencies": {
    "express": "^4.19.2"
  }
}
"@

$stubIndex = @"
const express = require("express");
const app = express();
app.use(express.json({ limit: "2mb" }));

app.get("/healthz", (_req, res) => res.status(200).send("ok"));

app.post("/telegram/events", (req, res) => {
  const env = req.body || {};
  const kind = env.kind || "unknown";
  const receipt = env.receipt_id || "no-receipt";
  const text = env?.payload?.text || "";

  let reply_text = "✅ upstream-stub got kind=" + kind + " receipt=" + receipt;
  if (text) {
    reply_text += ' text="' + String(text).slice(0, 80) + '"';
  }

  res.json({ reply_text });
});

app.listen(8080, () => console.log("upstream-stub listening on :8080"));
"@


Write-TextFileNoBom $stubDockerfilePath $stubDockerfile
Write-TextFileNoBom $stubPackagePath    $stubPackage
Write-TextFileNoBom $stubIndexPath      $stubIndex

# --------------------
# Gateway
# --------------------
$gwDockerfilePath = Join-Path $gatewayDir "Dockerfile"
$gwPackagePath    = Join-Path $gatewayDir "package.json"
$gwJsPath         = Join-Path $gatewayDir "gateway.js"

$gwDockerfile = @"
FROM node:20-slim
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --omit=dev
COPY gateway.js ./
CMD ["node", "gateway.js"]
"@

$gwPackage = @"
{
  "name": "telegram-gateway",
  "version": "1.0.0",
  "dependencies": {
    "telegraf": "^4.16.3",
    "axios": "^1.6.8",
    "crypto": "^1.0.1"
  }
}
"@

$gwJs = @"
const { Telegraf } = require("telegraf");
const axios = require("axios");
const crypto = require("crypto");

const TELEGRAM_BOT_TOKEN = (process.env.TELEGRAM_BOT_TOKEN || "").trim();
const UPSTREAM_URL = (process.env.UPSTREAM_URL || "").trim();
const UPSTREAM_TIMEOUT_MS = parseInt(process.env.UPSTREAM_TIMEOUT_MS || "30000", 10);
const TELEGRAM_MODE = (process.env.TELEGRAM_MODE || "polling").trim().toLowerCase();

const ALLOWED_USER_IDS = (process.env.ALLOWED_USER_IDS || "")
  .split(",")
  .map(s => s.trim())
  .filter(Boolean);

const ALLOWED_GROUP_IDS = (process.env.ALLOWED_GROUP_IDS || "")
  .split(",")
  .map(s => s.trim())
  .filter(Boolean);

function nowIso() { return new Date().toISOString(); }
function mkId() { return crypto.randomBytes(8).toString("hex"); }

if (!TELEGRAM_BOT_TOKEN) { console.error("FATAL: TELEGRAM_BOT_TOKEN missing"); process.exit(1); }
if (!UPSTREAM_URL) { console.error("FATAL: UPSTREAM_URL missing"); process.exit(1); }
if (ALLOWED_USER_IDS.length === 0) { console.error("FATAL: ALLOWED_USER_IDS missing/empty"); process.exit(1); }

console.log("--- Telegram Gateway (MVP1) ---");
console.log("mode:", TELEGRAM_MODE);
console.log("upstream:", UPSTREAM_URL);
console.log("allowed_user_ids:", ALLOWED_USER_IDS.join(","));
console.log("allowed_group_ids:", ALLOWED_GROUP_IDS.join(",") || "(none)");

const bot = new Telegraf(TELEGRAM_BOT_TOKEN);

function isAllowed(ctx) {
  const userId = ctx.from?.id?.toString();
  const chatId = ctx.chat?.id?.toString();
  const chatType = ctx.chat?.type;

  const userOk = userId && ALLOWED_USER_IDS.includes(userId);

  // DM: allow if user is allowed
  if (chatType === "private") return userOk;

  // Group: allow only if group is explicitly allowed AND user is allowed
  if (chatType === "group" || chatType === "supergroup") {
    const groupOk = chatId && ALLOWED_GROUP_IDS.includes(chatId);
    return userOk && groupOk;
  }

  return false;
}

async function forwardToUpstream(envelope) {
  const resp = await axios.post(UPSTREAM_URL, envelope, {
    timeout: UPSTREAM_TIMEOUT_MS,
    headers: { "Content-Type": "application/json" }
  });
  return resp.data;
}

async function buildEnvelope(ctx, kind, payload = {}) {
  return {
    receipt_id: mkId(),
    received_at: nowIso(),
    kind,
    from: {
      user_id: ctx.from?.id,
      username: ctx.from?.username,
      first_name: ctx.from?.first_name,
      last_name: ctx.from?.last_name
    },
    chat: {
      id: ctx.chat?.id,
      type: ctx.chat?.type,
      title: ctx.chat?.title
    },
    message: {
      message_id: ctx.message?.message_id,
      date: ctx.message?.date
    },
    payload
  };
}

async function ack(ctx, receiptId) {
  await ctx.reply(`✅ Received. Receipt: ${receiptId}`);
}

bot.command("status", async (ctx) => {
  if (!isAllowed(ctx)) return;
  await ctx.reply("✅ gateway alive; upstream=" + (UPSTREAM_URL || "(unset)"));
});

bot.on("text", async (ctx) => {
  if (!isAllowed(ctx)) return;

  const envelope = await buildEnvelope(ctx, "text", { text: ctx.message?.text || "" });

  try {
    const upstream = await forwardToUpstream(envelope);
    const reply = upstream?.reply_text;
    if (reply) return ctx.reply(String(reply).slice(0, 3500));
    return ack(ctx, envelope.receipt_id);
  } catch (e) {
    return ctx.reply(`⚠️ Upstream unavailable. Receipt: ${envelope.receipt_id}`);
  }
});

bot.on("location", async (ctx) => {
  if (!isAllowed(ctx)) return;

  const loc = ctx.message?.location;
  const envelope = await buildEnvelope(ctx, "location", {
    location: { latitude: loc?.latitude, longitude: loc?.longitude }
  });

  try {
    const upstream = await forwardToUpstream(envelope);
    const reply = upstream?.reply_text;
    if (reply) return ctx.reply(String(reply).slice(0, 3500));
    return ack(ctx, envelope.receipt_id);
  } catch (_e) {
    return ack(ctx, envelope.receipt_id);
  }
});

bot.launch()
  .then(async () => {
    const me = await bot.telegram.getMe();
    console.log(`READY: @${me.username}`);
  })
  .catch((e) => {
    console.error("Bot launch failed:", e?.message || e);
    process.exit(1);
  });

process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));
"@

Write-TextFileNoBom $gwDockerfilePath $gwDockerfile
Write-TextFileNoBom $gwPackagePath    $gwPackage
Write-TextFileNoBom $gwJsPath         $gwJs

# --------------------
# Verification output (no execution)
# --------------------
Write-Host ""
Write-Host "Created/updated files under:" $svcRoot
Get-ChildItem -Recurse -File $svcRoot | Select-Object FullName, Length | Format-Table -AutoSize

Write-Host ""
Write-Host "NEXT (manual):"
Write-Host "  1) Verify .env values (do NOT paste token here):"
Write-Host "     - TELEGRAM_BOT_TOKEN set"
Write-Host "     - ALLOWED_USER_IDS set"
Write-Host "  2) git add . && git commit -m 'Complete telegram-ingress service file scaffolding' && git push"
Write-Host "  3) On Linux: git pull (no Docker yet unless you choose to validate runtime)"
