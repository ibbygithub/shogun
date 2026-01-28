const express = require("express");
const bodyParser = require("body-parser");

const app = express();
app.use(bodyParser.json());

// ===== Tunables (DEBUG MODE) =====
const MOVE_THRESHOLD_METERS = 20;   // 👈 lowered for testing
const COOLDOWN_SECONDS = 10;        // 👈 lowered for testing

// ===== State (in-memory MVP) =====
const lastByChat = new Map();
// chatId → { lat, lon, ts, lastNotifyTs }

// ===== Helpers =====
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

function now() {
  return Math.floor(Date.now() / 1000);
}

// ===== Endpoint =====
app.post("/", (req, res) => {
  const ev = req.body;
  const chatId = ev?.chat?.id;

  if (!chatId) {
    console.log("[drop] missing chat id");
    return res.json({});
  }

  console.log(
    `[event] kind=${ev.kind} receipt=${ev.receipt_id} chat=${chatId}`,
    ev.payload?.location
      ? `lat=${ev.payload.location.latitude} lon=${ev.payload.location.longitude}`
      : ""
  );

  // Only act on location events
  if (ev.kind !== "location" || !ev.payload?.location) {
    return res.json({});
  }

  const lat = ev.payload.location.latitude;
  const lon = ev.payload.location.longitude;
  const ts = now();

  const prev = lastByChat.get(chatId);

  if (!prev) {
    lastByChat.set(chatId, {
      lat,
      lon,
      ts,
      lastNotifyTs: 0,
    });

    return res.json({
      reply_text: `📍 Location tracking started\nlat=${lat}\nlon=${lon}`,
    });
  }

  const moved = haversine(prev.lat, prev.lon, lat, lon);
  const sinceLast = ts - prev.ts;
  const sinceNotify = ts - prev.lastNotifyTs;

  const shouldNotify =
    moved >= MOVE_THRESHOLD_METERS &&
    sinceNotify >= COOLDOWN_SECONDS;

  console.log(
    `[eval] chat=${chatId} moved=${moved.toFixed(
      1
    )}m sinceLast=${sinceLast}s sinceNotify=${sinceNotify}s notify=${shouldNotify}`
  );

  // Update baseline every time
  prev.lat = lat;
  prev.lon = lon;
  prev.ts = ts;

  if (!shouldNotify) {
    lastByChat.set(chatId, prev);
    return res.json({});
  }

  prev.lastNotifyTs = ts;
  lastByChat.set(chatId, prev);

  return res.json({
    reply_text: `📍 Trigger fired\nmoved=${moved.toFixed(
      1
    )}m\nsinceLast=${sinceLast}s\nthreshold=${MOVE_THRESHOLD_METERS}m`,
  });
});

// ===== Boot =====
const PORT = 8080;
app.listen(PORT, () => {
  console.log(`upstream-stub listening on :${PORT}`);
});
