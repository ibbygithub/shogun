const express = require("express");
const app = express();

app.use(express.json({ limit: "2mb" }));

// ===== Tunables (DEBUG MODE) =====
const MOVE_THRESHOLD_METERS = 20; // easy test
const COOLDOWN_SECONDS = 10;      // easy test

// ===== State (in-memory MVP) =====
// chatId -> { lat, lon, lastTs, lastNotifyTs }
const state = new Map();

function nowSec() {
  return Math.floor(Date.now() / 1000);
}

// Haversine distance in meters
function haversine(lat1, lon1, lat2, lon2) {
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

// One handler, mounted on BOTH routes so we can’t mismatch again.
function handleTelegramEvent(req, res) {
  const ev = req.body || {};
  const kind = ev.kind || "unknown";
  const receipt = ev.receipt_id || "no-receipt";
  const chatId = ev.chat?.id;

  const loc = ev.payload?.location;
  const lat = loc?.latitude;
  const lon = loc?.longitude;

  console.log(
    `[event] kind=${kind} receipt=${receipt} chat=${chatId ?? "?"}` +
      (loc ? ` lat=${lat} lon=${lon}` : "")
  );

  if (!chatId) return res.json({});

  // Only do movement logic for location
  if (kind !== "location" || !loc) return res.json({});

  const ts = nowSec();
  const prev = state.get(chatId);

  if (!prev) {
    state.set(chatId, { lat, lon, lastTs: ts, lastNotifyTs: 0 });
    // This is the message you expected on start:
    return res.json({
      reply_text: `📍 Tracking started\nlat=${lat}\nlon=${lon}\n(threshold=${MOVE_THRESHOLD_METERS}m cooldown=${COOLDOWN_SECONDS}s)`,
    });
  }

  const moved = haversine(prev.lat, prev.lon, lat, lon);
  const sinceLast = ts - prev.lastTs;
  const sinceNotify = ts - prev.lastNotifyTs;

  const shouldNotify =
    moved >= MOVE_THRESHOLD_METERS && sinceNotify >= COOLDOWN_SECONDS;

  console.log(
    `[eval] chat=${chatId} moved=${moved.toFixed(1)}m sinceLast=${sinceLast}s sinceNotify=${sinceNotify}s notify=${shouldNotify}`
  );

  // update baseline each time
  prev.lat = lat;
  prev.lon = lon;
  prev.lastTs = ts;

  if (!shouldNotify) {
    state.set(chatId, prev);
    return res.json({});
  }

  prev.lastNotifyTs = ts;
  state.set(chatId, prev);

  return res.json({
    reply_text: `📍 Trigger fired\nmoved=${moved.toFixed(
      1
    )}m\nsinceLast=${sinceLast}s\nthreshold=${MOVE_THRESHOLD_METERS}m\ncooldown=${COOLDOWN_SECONDS}s`,
  });
}

// ✅ Accept both old and new paths
app.post("/", handleTelegramEvent);
app.post("/telegram/events", handleTelegramEvent);

const PORT = 8080;
app.listen(PORT, () => console.log(`upstream-stub listening on :${PORT}`));
