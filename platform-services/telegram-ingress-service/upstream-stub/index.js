const express = require("express");
const app = express();
app.use(express.json({ limit: "2mb" }));

app.get("/healthz", (_req, res) => res.status(200).send("ok"));

app.post("/telegram/events", (req, res) => {
  const env = req.body || {};
  const kind = env.kind || "unknown";
  const receipt = env.receipt_id || "no-receipt";
  const text = (env && env.payload && env.payload.text) ? String(env.payload.text) : "";

  const reply_text =
    "✅ upstream-stub got kind=" + kind +
    " receipt=" + receipt +
    (text ? ' text="' + text.slice(0, 80) + '"' : "");

  res.json({ reply_text });
});

app.listen(8080, () => console.log("upstream-stub listening on :8080"));
