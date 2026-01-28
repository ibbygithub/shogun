const express = require("express");
const app = express();

app.use(express.json({ limit: "2mb" }));

/**
 * In-memory state (MVP-safe)
 * Keyed by chat_id to avoid cross-chat bleed
 */
const state = new Map();

// Tunables (MVP defaults)
const MIN_DISTANCE_METERS = 100;
const MIN_NOTIFY_INTERVAL_MS = 60 * 1000;

function now() {
  return Date.now();
}

/**
 * Haversine distance in meters
 */
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

  let reply_text =
    "✅ upstream-stub got kind=" + kind + " receipt=" + receipt;

  // ----- TEXT -----
  if (kind === "text" && payload.text) {
    reply_text += ` text="${String(payload.text).slice(0, 80)}"`;
    return res.json({ reply_text });
  }

  // ----- PHOTO -----
  if (kind === "photo") {
    const caption = payload.caption
      ? ` caption="${String(payload.caption).slice(0, 80)}"`
      : "";
    const count = Array.isArray(payload.photos)
      ? ` photos=${payload.photos.length}`
      : "";
    reply_text += caption + count;
    return res.json({ reply_text });
  }

  // ----- VOICE -----
  if (kind === "voice" && payload.voice?.duration) {
    reply_text += ` duration=${payload.voice.duration}s`;
    return res.json({ reply_text });
  }

  // ----- LOCATION (THIS IS THE NEW SHOGUN LOGIC) -----
  if (kind === "location" && payload.location) {
    const { latitude, longitude } = payload.location;
    const ts = now();

    const prev = state.get(chatId);

    if (!prev) {
      // First location: store, but don't notify
      state.set(chatId, {
        lat: latitude,
        lon: longitude,
        lastNotified: 0,
      });

      reply_text += ` lat=${latitude} lon=${longitude}`;
      return res.json({ reply_text });
    }

    const moved = distanceMeters(
      prev.lat,
      prev.lon,
      latitude,
      longitude
    );

    const sinceLast = ts - prev.lastNotified;

    if (
      moved >= MIN_DISTANCE_METERS &&
      sinceLast >= MIN_NOTIFY_INTERVAL_MS
    ) {
      state.set(chatId, {
        lat: latitude,
        lon: longitude,
        lastNotified: ts,
      });

      return res.json({
        reply_text: `🚶 You moved ~${Math.round(
          moved
        )}m. Want food, coffee, or water?`,
      });
    }

    // Update location silently
    state.set(chatId, {
      lat: latitude,
      lon: longitude,
      lastNotified: prev.lastNotified,
    });

    reply_text += ` lat=${latitude} lon=${longitude}`;
    return res.json({ reply_text });
  }

  // ----- DEFAULT -----
  return res.json({ reply_text });
});

app.listen(8080, () =>
  console.log("upstream-stub listening on :8080")
);
