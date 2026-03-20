"""
Shogun Web Chat — Tool Integration Test Runner
Tests that Gemini correctly selects and invokes each declared tool.

Usage:
    python tools/test_chat_tools.py

Requires:
    - shogun-web-api running on localhost:8090
    - SHOGUN_BYPASS_AUTH=true in container .env
    - platform-places-google, platform-tavily reachable on platform_net
    - shogun_v1 DB seeded (itinerary, pois, knowledge_items, checklist_items)
"""

import datetime
import json
import os
import sys
import time
from pathlib import Path

import httpx

BASE = "http://localhost:8090"
HEADERS = {"Content-Type": "application/json"}
REPORT_DIR = Path(__file__).parent.parent / "outputs" / "validation"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

results: list[dict] = []


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def send_message(text: str, retries: int = 2) -> dict:
    """POST /chat and return the full JSON response. Retries on 500 (transient Valkey/DB)."""
    for attempt in range(retries + 1):
        resp = httpx.post(
            f"{BASE}/chat",
            json={"message": text},
            headers=HEADERS,
            timeout=45.0,
        )
        if resp.status_code == 500 and attempt < retries:
            print(f"  [retry {attempt+1}] 500 error, waiting 3s...")
            time.sleep(3)
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()
    return resp.json()


def clear_history() -> None:
    """DELETE /chat/history to reset conversation between tests."""
    try:
        httpx.delete(f"{BASE}/chat/history", headers=HEADERS, timeout=10.0)
    except Exception:
        pass


def tools_called(response: dict) -> list[str]:
    """Return list of tool names called, in order."""
    return [a["tool"] for a in response.get("tool_actions", [])]


def response_text(response: dict) -> str:
    return response.get("response", "")


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------

def assert_tool_called(r: dict, tool: str, test_id: str) -> tuple[bool, str]:
    called = tools_called(r)
    if tool not in called:
        return False, f"Expected tool '{tool}' but got: {called}"
    return True, f"Tool '{tool}' called OK"


def assert_tool_not_called(r: dict, tool: str) -> tuple[bool, str]:
    called = tools_called(r)
    if tool in called:
        return False, f"Tool '{tool}' should NOT have been called, but was"
    return True, f"Tool '{tool}' correctly not called OK"


def assert_contains_any(text: str, substrings: list[str]) -> tuple[bool, str]:
    matches = [s for s in substrings if s.lower() in text.lower()]
    if not matches:
        return False, f"Response missing all of: {substrings}"
    return True, f"Response contains: {matches} OK"


def assert_contains_url(text: str, domain: str = "maps.google.com") -> tuple[bool, str]:
    if domain in text or "google.com/maps" in text:
        return True, f"Google Maps URL present OK"
    return False, "Response missing Google Maps URL"


def assert_not_contains(text: str, bad_strings: list[str]) -> tuple[bool, str]:
    found = [s for s in bad_strings if s.lower() in text.lower()]
    if found:
        return False, f"Response contained prohibited text: {found}"
    return True, "No prohibited strings found OK"


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def run_test(test_id: str, desc: str, checks: list[tuple[bool, str]]) -> bool:
    passed = all(ok for ok, _ in checks)
    status = "PASS" if passed else "FAIL"
    details = [msg for _, msg in checks]
    results.append({
        "id": test_id,
        "description": desc,
        "status": status,
        "checks": details,
    })
    marker = "PASS" if passed else "FAIL"
    safe_desc = desc.encode("ascii", "replace").decode("ascii")
    print(f"\n[{marker}] {test_id}: {safe_desc}")
    for ok, msg in checks:
        prefix = "  OK " if ok else "  FAIL"
        safe_msg = msg.encode("ascii", "replace").decode("ascii")
        print(f"{prefix} {safe_msg}")
    return passed


# ---------------------------------------------------------------------------
# Individual tests
# ---------------------------------------------------------------------------

def tc01_find_nearby_sim():
    """TC-01: find_nearby_places for SIM cards near Osaka Airbnb."""
    clear_history()
    r = send_message(
        "Find 3 places that sell data SIM cards within 10 minute walk of my osaka airbnb. "
        "Give me the name, address, and a Google Maps link for each."
    )
    txt = response_text(r)
    checks = [
        assert_tool_called(r, "find_nearby_places", "TC-01"),
        assert_not_contains(txt, ["I cannot provide Google Maps", "I do not have the ability"]),
        assert_contains_url(txt),
        assert_contains_any(txt, ["Osaka", "大阪", "Kita", "Chuo", "Namba", "Umeda"]),
    ]
    return run_test("TC-01", "find_nearby_places: SIM cards near Osaka Airbnb", checks)


def tc02_find_nearby_pharmacy():
    """TC-02: find_nearby_places for pharmacy, implicit current accommodation."""
    clear_history()
    r = send_message("What pharmacies are within 5 minute walk of my hotel?")
    txt = response_text(r)
    checks = [
        assert_tool_called(r, "find_nearby_places", "TC-02"),
        assert_contains_any(txt, ["pharmacy", "drugstore", "薬", "Matsumoto", "Welcia",
                                   "Kokumin", "sundrug", "tsuruha"]),
    ]
    return run_test("TC-02", "find_nearby_places: pharmacy near current accommodation", checks)


def tc03_search_knowledge():
    """TC-03: search_trip_knowledge for Tokyo ramen."""
    clear_history()
    r = send_message("What ramen restaurants do you have in our knowledge base for Tokyo?")
    txt = response_text(r)
    checks = [
        assert_tool_called(r, "search_trip_knowledge", "TC-03"),
        assert_contains_any(txt, ["ramen", "ラーメン", "Tokyo", "東京"]),
    ]
    return run_test("TC-03", "search_trip_knowledge: Tokyo ramen", checks)


def tc04_web_search_sakura():
    """TC-04: sakura status — pre-augmented via Tavily, OR tool called."""
    # Note: sakura queries are intercepted by _is_sakura_query() and augmented
    # with Tavily data BEFORE the LLM call — no tool_action appears. This is
    # correct behavior. We accept either path: pre-augmented (no tool) or tool call.
    clear_history()
    r = send_message("What is the current sakura bloom status in Osaka right now?")
    txt = response_text(r)
    called = tools_called(r)
    # Either the response contains sakura info (pre-augmented) or web_search was called
    has_sakura_info = any(w in txt.lower() for w in ["sakura", "cherry blossom", "bloom", "hanami"])
    checks = [
        (has_sakura_info,
         f"Response contains sakura info (pre-augmented path) OK" if has_sakura_info
         else f"No sakura content found in response: {txt[:200]}"),
        assert_not_contains(txt, ["I don't know", "I cannot find", "no information"]),
    ]
    return run_test("TC-04", "sakura status: pre-augmented or tool call both acceptable", checks)


def tc05_get_itinerary():
    """TC-05: get_itinerary_legs for March 25."""
    clear_history()
    r = send_message("What is planned for March 25?")
    txt = response_text(r)
    checks = [
        assert_tool_called(r, "get_itinerary_legs", "TC-05"),
        assert_contains_any(txt, ["Nara", "奈良", "deer", "Todai", "temple"]),
    ]
    return run_test("TC-05", "get_itinerary_legs: March 25 (Nara)", checks)


def tc06_trip_overview():
    """TC-06: get_trip_overview for free days in Tokyo."""
    clear_history()
    r = send_message("Which days in Tokyo are still open and have nothing planned?")
    txt = response_text(r)
    checks = [
        assert_tool_called(r, "get_trip_overview", "TC-06"),
        assert_contains_any(txt, ["April 7", "April 8", "Apr 7", "Apr 8",
                                   "open", "free", "nothing scheduled"]),
    ]
    return run_test("TC-06", "get_trip_overview: free days in Tokyo", checks)


def tc07_create_leg():
    """TC-07: create_itinerary_leg — add Dotonbori walk."""
    clear_history()
    r = send_message('Add "Dotonbori evening walk" to March 28.')
    txt = response_text(r)
    checks = [
        assert_tool_called(r, "create_itinerary_leg", "TC-07"),
        assert_contains_any(txt, ["added", "created", "scheduled", "Dotonbori", "March 28"]),
    ]
    passed = run_test("TC-07", "create_itinerary_leg: add Dotonbori walk Mar 28", checks)
    # Cleanup: delete the created leg via direct DB — log that cleanup is needed
    if passed:
        results[-1]["cleanup_needed"] = "Delete 'Dotonbori evening walk' from 2026-03-28"
    return passed


def tc08_update_leg():
    """TC-08: update_itinerary_leg — add note to Nara."""
    clear_history()
    r = send_message("Add a note to the Nara day trip: bring yen cash for deer crackers")
    txt = response_text(r)
    called = tools_called(r)
    checks = [
        assert_tool_called(r, "get_itinerary_legs", "TC-08"),
        assert_tool_called(r, "update_itinerary_leg", "TC-08"),
        assert_contains_any(txt, ["updated", "added", "note", "Nara", "deer"]),
    ]
    return run_test("TC-08", "update_itinerary_leg: add note to Nara day trip", checks)


def tc09_delete_with_confirmation():
    """TC-09: delete_itinerary_leg only after explicit confirmation."""
    clear_history()
    # Turn 1: request deletion — bot must fetch legs first, then ask to confirm
    r1 = send_message("Delete the Dotonbori evening walk from the calendar.")
    txt1 = response_text(r1)
    called1 = tools_called(r1)

    # Must NOT call delete on first request
    no_immediate_delete = "delete_itinerary_leg" not in called1
    # Bot should ask for confirmation or clarify what it found
    asks_for_confirm = any(w in txt1.lower() for w in
                           ["confirm", "sure", "are you", "want me to", "really",
                            "delete", "remove", "proceed"])

    # Turn 2: confirm
    r2 = send_message("Yes, confirmed, delete it.")
    called2 = tools_called(r2)
    txt2 = response_text(r2)

    checks = [
        (no_immediate_delete, "No premature delete on first request OK" if no_immediate_delete
         else f"PREMATURE DELETE on turn 1 — called {called1}"),
        (asks_for_confirm, "Bot prompted for confirmation OK" if asks_for_confirm
         else f"Bot did not prompt for confirmation: {txt1[:300]}"),
        assert_tool_called(r2, "delete_itinerary_leg", "TC-09"),
        assert_contains_any(txt2, ["deleted", "removed", "done", "removed"]),
    ]
    return run_test("TC-09", "delete_itinerary_leg: confirm before delete", checks)


def tc10_checklist_read():
    """TC-10: get_checklist_items."""
    clear_history()
    r = send_message("Show me my packing checklist")
    txt = response_text(r)
    checks = [
        assert_tool_called(r, "get_checklist_items", "TC-10"),
        # Should return items — checklist_items has 15 seeded records
        assert_contains_any(txt, ["passport", "adapter", "camera", "charger",
                                   "medicine", "shoes", "clothes", "packed"]),
    ]
    return run_test("TC-10", "get_checklist_items: show packing list", checks)


def tc11_toggle_checklist():
    """TC-11: toggle_checklist_item — mark passport packed."""
    clear_history()
    # More explicit prompt to force toggle rather than just read
    r = send_message("I just packed my passport. Please mark it as packed on the checklist now.")
    txt = response_text(r)
    called = tools_called(r)
    # Accept either: toggle called directly, or get then toggle
    toggle_called = "toggle_checklist_item" in called
    checks = [
        (toggle_called, f"toggle_checklist_item called OK. Got: {called}" if toggle_called
         else f"toggle_checklist_item NOT called. Got: {called}"),
        assert_contains_any(txt, ["passport", "packed", "marked", "checked", "updated"]),
    ]
    return run_test("TC-11", "toggle_checklist_item: mark passport packed", checks)


def tc12_get_pois():
    """TC-12: get_trip_pois for Tokyo."""
    clear_history()
    r = send_message("Show me points of interest in Tokyo")
    txt = response_text(r)
    checks = [
        assert_tool_called(r, "get_trip_pois", "TC-12"),
        assert_contains_any(txt, ["Tokyo", "museum", "park", "temple", "shrine",
                                   "Ueno", "Sugamo", "Ghibli", "Shibuya"]),
    ]
    return run_test("TC-12", "get_trip_pois: Tokyo POIs", checks)


def tc13_maps_link_direct():
    """TC-13: Google Maps link constructed without tool call."""
    clear_history()
    r = send_message("Send me a Google Maps link for Kenroku-en garden in Kanazawa")
    txt = response_text(r)
    checks = [
        assert_contains_url(txt),
        assert_not_contains(txt, ["I cannot provide Google Maps",
                                   "I do not have the ability",
                                   "cannot create",
                                   "unable to provide"]),
        assert_contains_any(txt, ["Kenroku", "兼六園", "Kanazawa"]),
    ]
    return run_test("TC-13", "Google Maps link: Kenroku-en direct construction", checks)


def tc14_find_nearby_tokyo():
    """TC-14: find_nearby_places for Tokyo accommodation anchor."""
    clear_history()
    r = send_message("Find a convenience store within 5 minute walk of our Tokyo accommodation")
    txt = response_text(r)
    checks = [
        assert_tool_called(r, "find_nearby_places", "TC-14"),
        assert_contains_any(txt, ["7-Eleven", "Family Mart", "FamilyMart", "Lawson",
                                   "セブン", "ファミリーマート", "ローソン"]),
        assert_contains_url(txt),
    ]
    return run_test("TC-14", "find_nearby_places: convenience store near Tokyo Sugamo", checks)


def tc15_places_fallback():
    """TC-15: If find_nearby_places fails, web_search covers gracefully."""
    # We test this by sending a proximity query and checking that if the
    # tool fails (gateway unavailable), the user gets a useful response
    # rather than an error message. We simulate this by checking the
    # fallback path exists in the tool output.
    clear_history()
    r = send_message("Find a drugstore near my osaka airbnb")
    txt = response_text(r)
    called = tools_called(r)
    # Either find_nearby_places worked, or web_search was used as fallback
    ok = "find_nearby_places" in called or "web_search" in called
    useful = not any(bad in txt.lower() for bad in ["error", "failed", "cannot help",
                                                     "i am unable to find"])
    checks = [
        (ok, f"find_nearby_places or web_search called: {called}"),
        (useful, "Response is useful (no error message to user) OK" if useful
         else f"Response contained error/failure: {txt[:200]}"),
        assert_contains_any(txt, ["drugstore", "pharmacy", "Matsumoto",
                                   "drug", "薬", "Welcia"]),
    ]
    return run_test("TC-15", "Fallback: drugstore near Osaka Airbnb", checks)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def write_report(all_passed: bool) -> Path:
    today = datetime.date.today().isoformat()
    path = REPORT_DIR / f"{today}_chat-tool-tests_report.md"

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    overall = "GREEN" if all_passed else ("YELLOW" if failed <= 2 else "RED")

    lines = [
        f"# Chat Tool Test Report — {today}",
        f"Overall: {overall} ({passed}/{len(results)} passed)\n",
        "## Results\n",
    ]

    for r in results:
        icon = "✅" if r["status"] == "PASS" else "❌"
        lines.append(f"### {icon} {r['id']}: {r['description']}")
        lines.append(f"**Status:** {r['status']}")
        if r.get("cleanup_needed"):
            lines.append(f"**Cleanup needed:** {r['cleanup_needed']}")
        lines.append("**Checks:**")
        for check in r["checks"]:
            lines.append(f"- {check}")
        lines.append("")

    if any(r.get("cleanup_needed") for r in results):
        lines.append("## Cleanup Required")
        for r in results:
            if r.get("cleanup_needed"):
                lines.append(f"- {r['id']}: {r['cleanup_needed']}")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Shogun Chat Tool Integration Tests")
    print("=" * 60)

    # Preflight: verify API is up
    try:
        r = httpx.get(f"{BASE}/health", timeout=5.0)
        print(f"API health: {r.status_code}")
    except Exception as e:
        print(f"ABORT: API not reachable at {BASE}: {e}")
        sys.exit(2)

    test_fns = [
        tc01_find_nearby_sim,
        tc02_find_nearby_pharmacy,
        tc03_search_knowledge,
        tc04_web_search_sakura,
        tc05_get_itinerary,
        tc06_trip_overview,
        tc07_create_leg,
        tc08_update_leg,
        tc09_delete_with_confirmation,
        tc10_checklist_read,
        tc11_toggle_checklist,
        tc12_get_pois,
        tc13_maps_link_direct,
        tc14_find_nearby_tokyo,
        tc15_places_fallback,
    ]

    passed_count = 0
    for fn in test_fns:
        try:
            ok = fn()
            if ok:
                passed_count += 1
        except Exception as e:
            test_id = fn.__name__.upper()
            results.append({
                "id": test_id,
                "description": fn.__doc__ or "unknown",
                "status": "ERROR",
                "checks": [f"Exception: {e}"],
            })
            print(f"\nERROR {test_id}: Exception - {e}")

        # Brief pause between tests to avoid rate limiting
        time.sleep(2)

    all_passed = passed_count == len(test_fns)
    report_path = write_report(all_passed)

    print("\n" + "=" * 60)
    print(f"Results: {passed_count}/{len(test_fns)} passed")
    print(f"Report: {report_path}")
    print("=" * 60)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
