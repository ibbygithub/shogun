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
  await ctx.reply(âœ… Received. Receipt: );
}

bot.command("status", async (ctx) => {
  if (!isAllowed(ctx)) return;
  await ctx.reply("âœ… gateway alive; upstream=" + (UPSTREAM_URL || "(unset)"));
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
    return ctx.reply(âš ï¸ Upstream unavailable. Receipt: );
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
    console.log(READY: @);
  })
  .catch((e) => {
    console.error("Bot launch failed:", e?.message || e);
    process.exit(1);
  });

process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));