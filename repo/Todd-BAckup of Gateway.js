const { Telegraf } = require("telegraf");
const axios = require("axios");
const crypto = require("crypto");

const BOT_TOKEN = (process.env.TELEGRAM_BOT_TOKEN || "").trim();
const UPSTREAM_URL = (process.env.UPSTREAM_URL || "").trim();
const TIMEOUT_MS = parseInt(process.env.UPSTREAM_TIMEOUT_MS || "30000", 10);

const ALLOWED_USER_IDS = (process.env.ALLOWED_USER_IDS || "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);

if (!BOT_TOKEN) {
  console.error("FATAL: TELEGRAM_BOT_TOKEN missing");
  process.exit(1);
}
if (!UPSTREAM_URL) {
  console.error("FATAL: UPSTREAM_URL missing");
  process.exit(1);
}
if (ALLOWED_USER_IDS.length === 0) {
  console.error("FATAL: ALLOWED_USER_IDS empty");
  process.exit(1);
}

function nowIso() {
  return new Date().toISOString();
}

function mkId() {
  return crypto.randomBytes(8).toString("hex");
}

function isAllowed(ctx) {
  const userId = ctx.from && ctx.from.id ? String(ctx.from.id) : null;
  return userId && ALLOWED_USER_IDS.includes(userId);
}

async function forward(envelope) {
  const resp = await axios.post(UPSTREAM_URL, envelope, {
    timeout: TIMEOUT_MS,
    headers: { "Content-Type": "application/json" },
  });
  return resp.data;
}

const bot = new Telegraf(BOT_TOKEN);

bot.command("status", async (ctx) => {
  if (!isAllowed(ctx)) return;
  await ctx.reply("✅ gateway alive");
});

bot.on("text", async (ctx) => {
  if (!isAllowed(ctx)) return;

  const envelope = {
    receipt_id: mkId(),
    received_at: nowIso(),
    kind: "text",
    from: { user_id: ctx.from.id },
    payload: { text: ctx.message.text },
  };

  try {
    const upstream = await forward(envelope);
    if (upstream && upstream.reply_text) {
      await ctx.reply(String(upstream.reply_text));
    } else {
      await ctx.reply("✅ received");
    }
  } catch (_err) {
    await ctx.reply("⚠️ upstream unavailable");
  }
});

bot.launch()
  .then(() => console.log("gateway ready"))
  .catch((err) => {
    console.error("launch failed:", err);
    process.exit(1);
  });

process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));
sysadmin-agent@svcnode-01:/opt/git/work/shogun/platform-services/telegram-ingress-service/gateway$
