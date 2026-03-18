# Morning Brief Feature — Validation Report
**Date:** 2026-03-16
**Feature:** Daily 7:00 AM JST morning Telegram brief with APScheduler
**Branch:** develop

---

## Changes Made

### 1. requirements.txt
- Added `apscheduler==3.10.4`

### 2. app/services/brief.py (new file)
- Created morning brief service
- Sends to all users with `notification_active = TRUE`
- Notify window: 2026-03-16 (1 week before departure) through 2026-04-09 (end of trip)
- Outside window: logs and returns silently — no send
- Pre-trip header: "Japan in N days!" countdown
- Trip header: "Day N of 18"
- Pulls today's itinerary legs from `trip_itinerary` (date_local, leg_sequence order)
- Infers current city from most recent itinerary row (excluding SFO/LAX)
- Fetches weather via existing `weather_svc.get_weather_for_city()` for Japan cities
- City emoji map: osaka/nara/kanazawa/tokyo/san francisco/los angeles
- Sends via `sender.send_message()` with Markdown parse mode

### 3. app/main.py
- Added APScheduler imports: `AsyncIOScheduler`, `CronTrigger`
- Added `from app.services.brief import send_morning_brief`
- Lifespan startup: creates `AsyncIOScheduler`, adds cron job `hour=22, minute=0, timezone="UTC"` (= 07:00 JST)
- Job id: `morning_brief`, `replace_existing=True`
- Lifespan shutdown: `scheduler.shutdown(wait=False)`
- Added `GET /debug/morning-brief` endpoint for manual trigger testing

---

## Build Verification

```
docker compose build --no-cache  → SUCCESS
docker compose up -d             → Container started
```

### Container Logs (startup)
```
2026-03-16 06:12:45,010 INFO app.main DB connection OK (shogun_v1 @ platform-postgres)
2026-03-16 06:12:45,012 INFO apscheduler.scheduler Adding job tentatively -- it will be properly scheduled when the scheduler starts
2026-03-16 06:12:45,013 INFO apscheduler.scheduler Added job "send_morning_brief" to job store "default"
2026-03-16 06:12:45,013 INFO apscheduler.scheduler Scheduler started
2026-03-16 06:12:45,013 INFO app.main Morning brief scheduler started (fires at 22:00 UTC = 7:00 AM JST)
INFO:     Application startup complete.
```

### Health Check
```
GET http://localhost:8082/health
{"ok":true,"service":"shogun-core","version":"0.4.0"}
```

---

## Notes

- The collation version mismatch warning on DB connect is pre-existing, not introduced by this change.
- The `/debug/morning-brief` endpoint will silently return `{"ok": true}` if today is outside the notify window (2026-03-16 to 2026-04-09). Once the notify window opens (today is 2026-03-16), it will attempt to send to active users.
- Weather fetch only runs for Japan cities (osaka, nara, kanazawa, tokyo). Pre-trip dates will likely return no city from the itinerary query, so weather block is skipped.

---

## Status: PASS
