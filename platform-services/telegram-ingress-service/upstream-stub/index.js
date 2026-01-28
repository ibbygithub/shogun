const express = require("express");
const app = express();

app.use(express.json({ limit: "2mb" }));

app.get("/healthz", (_req, res) => res.status(200).send("ok"));

app.post("/telegram/events", (req, res) => {
  const env = req.body || {};
  const kind = env.kind || "unknown";
  const receipt = env.receipt_id || "no-receipt";
  const payload = env.payload || {};

  let details = "";

  switch (kind) {
    case "text": {
      if (payload.text) {
        details = ` text="${String(payload.text).slice(0, 80)}"`;
      }
      break;
    }

    case "photo": {
      const caption = payload.caption
        ? ` caption="${String(payload.caption).slice(0, 80)}"`
        : "";
      const count = Array.isArray(payload.photos)
        ? ` photos=${payload.photos.length}`
        : "";
      details = caption + count;
      break;
    }

    case "location": {
      if (payload.location) {
        const { latitude, longitude, live_period } = payload.location;
        details =
          ` lat=${latitude} lon=${longitude}` +
          (live_period ? ` live_period=${live_period}s` : "");
      }
      break;
    }

    case "voice": {
      if (payload.voice && payload.voice.duration) {
        details = ` duration=${payload.voice.duration}s`;
      }
      break;
    }

    default:
      // keep generic for now
      break;
  }

  const reply_text =
    "✅ upstream-stub got kind=" +
    kind +
    " receipt=" +
    receipt +
    details;

  res.json({ reply_text });
});

app.listen(8080, () =>
  console.log("upstream-stub listening on :8080")
);
