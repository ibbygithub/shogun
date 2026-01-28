// LIVE-LOCATION-FIX: edited_message.location forwarded as kind=location (proof line)

const { Telegraf } = require("telegraf");
const axios = require("axios");
const crypto = require("crypto");

// ===== Env =====
const BOT_TOKEN = (process.env.TELEGRAM_BOT_TOKEN || "").trim();
const UPSTREAM_URL = (process.env.UPSTREAM_URL || "").trim();
const TIMEOUT_MS = parseInt(process.env.UPSTREAM_TIMEOUT_MS || "30000", 10);

// Ingress slider (default polling)
const TELEGRAM_MODE = (process.env.TELEGRAM_MODE || "polling").trim().toLowerCase();

// Webhook settings (only used if TELEGRAM_MODE=webhook later)
const WEBHOOK_DOMAIN = (process.env.WEBHOOK_DOMAIN || "").trim();
const WEBHOOK_PATH = (process.env.WEBHOOK_PATH || "/telegram/webhook").trim();
const WEBHOOK_PORT = parseInt(process.env.WEBHOOK_PORT || "3000", 10);

// Capability flags
const CAP_CAN_SEARCH = (process.env.CAP_CAN_SEARCH || "false").trim().toLowerCase() === "true";
const CAP_CAN_SCRAPE = (process.env.CAP_CAN_SCRAPE || "false").trim().toLowerCase() === "true";
const CAP_CAN_FETCH_FILES = (process.env.CAP_CAN_FETCH_FILES || "false").trim().toLowerCase() === "true";

// Allow lists
const ALLOWED_USER_IDS = (process.env.ALLOWED_USER_IDS || "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);

const ALLOWED_GROUP_IDS = (process.env.ALLOWED_GROUP_IDS || "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);

// ===== Guards =====
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
if (TELEGRAM_MODE === "webhook") {
  if (!WEBHOOK_DOMAIN) {
    console.error("FATAL: TELEGRAM_MODE=webhook requires WEBHOOK_DOMAIN");
    process.exit(1);
  }
  if (!WEBHOOK_PATH.startsWith("/")) {
    console.error("FATAL: WEBHOOK_PATH must start with '/'");
    process.exit(1);
  }
}

// ===== Helpers =====
function nowIso() {
  return new Date().toISOString();
}
function mkId() {
  return crypto.randomBytes(8).toString("hex");
}
function clip(s, n = 3500) {
  const str = String(s ?? "");
  return str.length > n ? str.slice(0, n) : str;
}

function isAllowed(ctx) {
  const userId = ctx.from?.id ? String(ctx.from.id) : null;
  const chatId = ctx.chat?.id ? String(ctx.chat.id) : null;
  const chatType = ctx.chat?.type;

  const userOk = userId && ALLOWED_USER_IDS.includes(userId);

  if (chatType === "private") return userOk;

  if (chatType === "group" || chatType === "supergroup") {
    const groupOk = chatId && ALLOWED_GROUP_IDS.includes(chatId);
    return userOk && groupOk;
  }

  return false;
}

async function forward(envelope) {
  const resp = await axios.post(UPSTREAM_URL, envelope, {
    timeout: TIMEOUT_MS,
    headers: { "Content-Type": "application/json" },
  });
  return resp.data;
}

function baseEnvelope(ctx, kind) {
  return {
    receipt_id: mkId(),
    received_at: nowIso(),
    kind,
    update: { update_id: ctx.update?.update_id },
    from: {
      user_id: ctx.from?.id,
      username: ctx.from?.username,
      first_name: ctx.from?.first_name,
      last_name: ctx.from?.last_name,
      language_code: ctx.from?.language_code,
    },
    chat: {
      id: ctx.chat?.id,
      type: ctx.chat?.type,
      title: ctx.chat?.title,
    },
    message: {
      message_id: ctx.message?.message_id,
      date: ctx.message?.date,
      reply_to_message_id: ctx.message?.reply_to_message?.message_id,
    },
    capabilities: {
      can_search: CAP_CAN_SEARCH,
      can_scrape: CAP_CAN_SCRAPE,
      can_fetch_files: CAP_CAN_FETCH_FILES,
    },
    payload: {},
  };
}

async function replyOrAck(ctx, receiptId, upstream) {
  const reply = upstream?.reply_text;
  if (reply) return ctx.reply(clip(reply));
  return ctx.reply(`✅ Received. Receipt: ${receiptId}`);
}

async function replyUpstreamDown(ctx, receiptId) {
  return ctx.reply(`⚠️ Upstream unavailable. Receipt: ${receiptId}`);
}

// ===== Payload builders =====
function locationPayloadFromLoc(loc) {
  return loc
    ? {
        location: {
          latitude: loc.latitude,
          longitude: loc.longitude,
          horizontal_accuracy: loc.horizontal_accuracy,
          live_period: loc.live_period,
          heading: loc.heading,
          proximity_alert_radius: loc.proximity_alert_radius,
        },
      }
    : { location: null };
}

function locationPayload(msg) {
  return locationPayloadFromLoc(msg?.location);
}

function photoPayload(msg) {
  const photos = Array.isArray(msg?.photo) ? msg.photo : [];
  return {
    caption: msg?.caption || "",
    photos: photos.map((p) => ({
      file_id: p.file_id,
      file_unique_id: p.file_unique_id,
      width: p.width,
      height: p.height,
      file_size: p.file_size,
    })),
  };
}

function documentPayload(msg) {
  const d = msg?.document;
  return {
    caption: msg?.caption || "",
    document: d
      ? {
          file_id: d.file_id,
          file_unique_id: d.file_unique_id,
          file_name: d.file_name,
          mime_type: d.mime_type,
          file_size: d.file_size,
        }
      : null,
  };
}

function voicePayload(msg) {
  const v = msg?.voice;
  return {
    voice: v
      ? {
          file_id: v.file_id,
          file_unique_id: v.file_unique_id,
          duration: v.duration,
          mime_type: v.mime_type,
          file_size: v.file_size,
        }
      : null,
  };
}

function audioPayload(msg) {
  const a = msg?.audio;
  return {
    audio: a
      ? {
          file_id: a.file_id,
          file_unique_id: a.file_unique_id,
          duration: a.duration,
          performer: a.performer,
          title: a.title,
          mime_type: a.mime_type,
          file_size: a.file_size,
        }
      : null,
  };
}

// ===== Bot =====
const bot = new Telegraf(BOT_TOKEN);

bot.command("status", async (ctx) => {
  if (!isAllowed(ctx)) return;
  await ctx.reply("✅ gateway alive; mode=" + TELEGRAM_MODE);
});

bot.on("text", async (ctx) => {
  if (!isAllowed(ctx)) return;

  const env = baseEnvelope(ctx, "text");
  env.payload = {
    text: ctx.message?.text || "",
    entities: ctx.message?.entities || [],
  };

  try {
    const upstream = await forward(env);
    await replyOrAck(ctx, env.receipt_id, upstream);
  } catch {
    await replyUpstreamDown(ctx, env.receipt_id);
  }
});

bot.on("location", async (ctx) => {
  if (!isAllowed(ctx)) return;

  const env = baseEnvelope(ctx, "location");
  env.payload = locationPayload(ctx.message);

  try {
    const upstream = await forward(env);
    await replyOrAck(ctx, env.receipt_id, upstream);
  } catch {
    await ctx.reply(`✅ Location received. Receipt: ${env.receipt_id}`);
  }
});

bot.on("photo", async (ctx) => {
  if (!isAllowed(ctx)) return;

  const env = baseEnvelope(ctx, "photo");
  env.payload = photoPayload(ctx.message);

  try {
    const upstream = await forward(env);
    await replyOrAck(ctx, env.receipt_id, upstream);
  } catch {
    await ctx.reply(`✅ Photo received. Receipt: ${env.receipt_id}`);
  }
});

bot.on("document", async (ctx) => {
  if (!isAllowed(ctx)) return;

  const env = baseEnvelope(ctx, "document");
  env.payload = documentPayload(ctx.message);

  try {
    const upstream = await forward(env);
    await replyOrAck(ctx, env.receipt_id, upstream);
  } catch {
    await ctx.reply(`✅ Document received. Receipt: ${env.receipt_id}`);
  }
});

bot.on("voice", async (ctx) => {
  if (!isAllowed(ctx)) return;

  const env = baseEnvelope(ctx, "voice");
  env.payload = voicePayload(ctx.message);

  try {
    const upstream = await forward(env);
    await replyOrAck(ctx, env.receipt_id, upstream);
  } catch {
    await ctx.reply(`✅ Voice received. Receipt: ${env.receipt_id}`);
  }
});

bot.on("audio", async (ctx) => {
  if (!isAllowed(ctx)) return;

  const env = baseEnvelope(ctx, "audio");
  env.payload = audioPayload(ctx.message);

  try {
    const upstream = await forward(env);
    await replyOrAck(ctx, env.receipt_id, upstream);
  } catch {
    await ctx.reply(`✅ Audio received. Receipt: ${env.receipt_id}`);
  }
});

// ✅ KEY FIX: Live location updates arrive as edited_message with edited.location
bot.on("edited_message", async (ctx) => {
  const edited = ctx.update?.edited_message;
  if (!edited) return;

  // allow check (private + group)
  const userId = edited.from?.id ? String(edited.from.id) : null;
  const chatIdStr = edited.chat?.id ? String(edited.chat.id) : null;
  const chatType = edited.chat?.type;

  const userOk = userId && ALLOWED_USER_IDS.includes(userId);
  if (!userOk) return;

  if (chatType === "group" || chatType === "supergroup") {
    const groupOk = chatIdStr && ALLOWED_GROUP_IDS.includes(chatIdStr);
    if (!groupOk) return;
  }

  // If edited message contains a location, forward it as kind=location
  if (edited.location) {
    const env = {
      receipt_id: mkId(),
      received_at: nowIso(),
      kind: "location",
      update: { update_id: ctx.update?.update_id },
      from: {
        user_id: edited.from?.id,
        username: edited.from?.username,
        first_name: edited.from?.first_name,
        last_name: edited.from?.last_name,
        language_code: edited.from?.language_code,
      },
      chat: {
        id: edited.chat?.id,
        type: edited.chat?.type,
        title: edited.chat?.title,
      },
      message: {
        message_id: edited.message_id,
        date: edited.date,
        edit_date: edited.edit_date,
      },
      capabilities: {
        can_search: CAP_CAN_SEARCH,
        can_scrape: CAP_CAN_SCRAPE,
        can_fetch_files: CAP_CAN_FETCH_FILES,
      },
      payload: locationPayloadFromLoc(edited.location),
    };

    try {
      await forward(env);
    } catch {
      // silent
    }
  }
});

async function start() {
  if (TELEGRAM_MODE === "webhook") {
    console.log("Starting in webhook mode");
    await bot.launch({
      webhook: { domain: WEBHOOK_DOMAIN, hookPath: WEBHOOK_PATH, port: WEBHOOK_PORT },
    });
  } else {
    console.log("Starting in polling mode");
    await bot.launch();
  }
  console.log("gateway ready");
}

start().catch((err) => {
  console.error("launch failed:", err?.message || err);
  process.exit(1);
});

process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));
