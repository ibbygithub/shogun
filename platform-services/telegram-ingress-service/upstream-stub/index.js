const express = require("express");
const app = express();

app.use(express.json({ limit: "2mb" }));

// In-memory state (MVP only)
const state = new Map();

// Tunables
const MIN_DISTANCE_METERS = 100;
const MIN_NOTIFY_INTERVAL_MS = 60 * 1000;

function nowMs() {
  return Date.now();
}

// Haversine distance in meters
function distanceMeters(lat1, lon1, lat2, lon2) {
  const R = 6371000;
  const toRad = (d) => (d * Math.PI) / 180;

  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) ** 2;

  return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

app.get("/healthz", (_req, res) => res.status(200).send("ok"));

app.post("/telegram/events", (req, res) => {
  const env = req.body || {};
  const kind = env.kind || "unknown";
  const receipt = env.receipt_id || "no-receipt";
  const payload = env.payload || {};
  const chatId = env.chat?.id || "unknown-chat";

  // Always log the event (so you can prove updates are arriving)
  console.log(
    `[event] kind=${kind} receipt=${receipt} chat=${chatId}` +
      (payload.location
        ? ` lat=${payload.location.latitude} lon=${payload.location.longitude}`
        : "") +
      (payload.caption
        ? ` caption="${String(payload.caption).slice(0, 40)}"`
        : "") +
      (payload.text
        ? ` text="${String(payload.text).slice(0, 40)}"`
        : "")
  );

  // TEXT
  if (kind === "text" && payload.text) {
    return res.json({
      reply_text: `✅ upstream-stub got kind=text receipt=${receipt} text="${String(
        payload.text
      ).slice(0, 80)}"`,
    });
  }

  // PHOTO
  if (kind === "photo") {
    const caption = payload.caption
      ? ` caption="${String(payload.caption).slice(0, 80)}"`
      : "";
    const count = Array.isArray(payload.photos)
      ? ` photos=${payload.photos.length}`
      : "";
    return res.json({
      reply_text: `✅ upstream-stub got kind=photo receipt=${receipt}${caption}${count}`,
    });
  }

  // VOICE
  if (kind === "voice" && payload.voice?.duration) {
    return res.json({
      reply_text: `✅ upstream-stub got kind=voice receipt=${receipt} duration=${payload.voice.duration}s`,
    });
  }

  // LOCATION (notify ONLY on trigger)
  if (kind === "location" && payload.location) {
    const { latitude, longitude } = payload.location;
    const ts = nowMs();

    const prev = state.get(chatId);

    if (!prev) {
      state.set(chatId, {
        lat: latitude,
        lon: longitude,
        lastNotified: 0,
      });
      // No reply_text -> gateway will not send any Telegram message.
      return res.json({});
    }

    const moved = distanceMeters(prev.lat, prev.lon, latitude, longitude);
    const sinceLastMs = ts - prev.lastNotified;

    const shouldNotify =
      moved >= MIN_DISTANCE_METERS && sinceLastMs >= MIN_NOTIFY_INTERVAL_MS;

    state.set(chatId, {
      lat: latitude,
      lon: longitude,
      lastNotified: shouldNotify ? ts : prev.lastNotified,
    });

    if (shouldNotify) {
      return res.json({
        reply_text: `🚶 You moved ~${Math.round(
          moved
        )}m. Want food, coffee, or water?`,
      });
    }

    return res.json({});
  }

  // DEFAULT
  return res.json({
    reply_text: `✅ upstream-stub got kind=${kind} receipt=${receipt}`,
  });
});

app.listen(8080, () => console.log("upstream-stub listening on :8080"));
