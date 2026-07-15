# -*- coding: utf-8 -*-
"""Multi-stream HTTP API test (10.1 + 10.2)"""
import json, time, sys
import urllib.request, urllib.error

BASE = "http://localhost:8080"
TOKEN = None  # will be set after login
p = 0  # passed
f = 0  # failed

def api(method, path, data=None, auth=False):
    url = BASE + path
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if auth and TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        b = e.read().decode() if e.fp else str(e)
        try: return json.loads(b)
        except: return {"success": False, "code": e.code, "message": b}
    except Exception as e:
        return {"success": False, "error": str(e)}

def ok(name, cond, detail=""):
    global p, f
    if cond:
        p += 1
        print("  [PASS] " + name + (" -- " + detail if detail else ""))
    else:
        f += 1
        print("  [FAIL] " + name + (" -- " + detail if detail else ""))

def ensure(name):
    streams = api("GET", "/api/admin/streams")
    for s in streams.get("data", {}).get("streams", []):
        if s["name"] == name:
            return s["id"]
    result = api("POST", "/api/admin/streams", {
        "name": name, "url": "rtmp://localhost/live/test",
        "type": "rtmp", "description": "Test - " + name, "enabled": True
    }, auth=True)
    return (result.get("data") or result).get("id")

def test_101():
    print("\n" + "=" * 50)
    print("10.1 Judge Management (Multi-Stream)")
    print("=" * 50)

    s1 = ensure("stream-1-test")
    s2 = ensure("stream-2-test")
    print("  stream-1: " + str(s1))
    print("  stream-2: " + str(s2))
    ok("stream-1 created", s1 is not None)
    ok("stream-2 created", s2 is not None)
    ok("s1 != s2", s1 != s2)

    # Save judges for s1
    print("\n  [Step] Save 3 judges for stream-1...")
    j1 = [
        {"name": "Prof Zhang", "role": "Ethicist", "avatar": "A1"},
        {"name": "Dr Li", "role": "Sociologist", "avatar": "A2"},
        {"name": "Lawyer Wang", "role": "Legal", "avatar": "A3"},
    ]
    r = api("POST", "/api/admin/judges", {"streamId": s1, "judges": j1}, auth=True)
    ok("s1 save judges", r.get("success"))
    ok("s1 3 judges", len(r.get("data", {}).get("judges", [])) == 3)

    # Save judges for s2
    print("\n  [Step] Save 3 different judges for stream-2...")
    j2 = [
        {"name": "Teacher Zhao", "role": "Education", "avatar": "B1"},
        {"name": "Dir Qian", "role": "Psychology", "avatar": "B2"},
        {"name": "Dean Sun", "role": "Medicine", "avatar": "B3"},
    ]
    r = api("POST", "/api/admin/judges", {"streamId": s2, "judges": j2}, auth=True)
    ok("s2 save judges", r.get("success"))
    ok("s2 3 judges", len(r.get("data", {}).get("judges", [])) == 3)

    # Verify dashboard isolation
    print("\n  [Step] Verify dashboard isolation...")
    d1 = api("GET", "/api/admin/dashboard?stream_id=" + s1)
    d2 = api("GET", "/api/admin/dashboard?stream_id=" + s2)
    dj1 = d1.get("data", {}).get("judges", [])
    dj2 = d2.get("data", {}).get("judges", [])
    ok("dash s1 3 judges", len(dj1) == 3, "got " + str(len(dj1)))
    ok("dash s2 3 judges", len(dj2) == 3, "got " + str(len(dj2)))
    ok("s1 has Prof Zhang", any(j.get("name") == "Prof Zhang" for j in dj1))
    ok("s2 has Teacher Zhao", any(j.get("name") == "Teacher Zhao" for j in dj2))

    # Update s1 judges, verify s2 unchanged
    print("\n  [Step] Update stream-1 judges, verify s2 unchanged...")
    j1u = [
        {"name": "Prof Zhang UPDATED", "role": "Chief Ethicist", "avatar": "A1"},
        {"name": "Dr Li", "role": "Sociologist", "avatar": "A2"},
        {"name": "Lawyer Wang", "role": "Legal", "avatar": "A3"},
    ]
    r = api("POST", "/api/admin/judges", {"streamId": s1, "judges": j1u}, auth=True)
    ok("s1 update OK", r.get("success"))

    d1u = api("GET", "/api/admin/dashboard?stream_id=" + s1)
    d2u = api("GET", "/api/admin/dashboard?stream_id=" + s2)
    ok("s1 name updated",
       any("UPDATED" in j.get("name", "") for j in d1u.get("data", {}).get("judges", [])))
    ok("s2 unchanged",
       not any("UPDATED" in j.get("name", "") for j in d2u.get("data", {}).get("judges", [])),
       "s2 should not have UPDATED judge")

    # Restore s1
    api("POST", "/api/admin/judges", {"streamId": s1, "judges": j1}, auth=True)

def test_102():
    print("\n" + "=" * 50)
    print("10.2 Debate Flow Control (Multi-Stream)")
    print("=" * 50)

    s1 = ensure("stream-1-test")
    s2 = ensure("stream-2-test")

    # Save flow for s1
    print("\n  [Step] Save debate flow for stream-1...")
    flow1 = [
        {"name": "Opening Statement L", "duration": 240, "side": "left", "order": 1},
        {"name": "Cross Exam R", "duration": 180, "side": "right", "order": 2},
        {"name": "Free Debate", "duration": 600, "side": "both", "order": 3},
    ]
    r = api("POST", "/api/admin/debate-flow", {"streamId": s1, "flow": flow1}, auth=True)
    ok("s1 save flow", r.get("success"))
    f1 = r.get("data", {}).get("flow", [])
    ok("s1 3 segments", len(f1) == 3, "got " + str(len(f1)))

    # Save different flow for s2
    print("\n  [Step] Save different debate flow for stream-2...")
    flow2 = [
        {"name": "Opening All", "duration": 300, "side": "both", "order": 1},
        {"name": "Cross Debate", "duration": 480, "side": "both", "order": 2},
        {"name": "Summary", "duration": 240, "side": "both", "order": 3},
        {"name": "Q&A", "duration": 360, "side": "both", "order": 4},
    ]
    r = api("POST", "/api/admin/debate-flow", {"streamId": s2, "flow": flow2}, auth=True)
    ok("s2 save flow", r.get("success"))
    f2 = r.get("data", {}).get("flow", [])
    ok("s2 4 segments", len(f2) == 4, "got " + str(len(f2)))

    # Verify isolation
    print("\n  [Step] Verify flow isolation...")
    g1 = api("GET", "/api/admin/debate-flow?stream_id=" + s1)
    g2 = api("GET", "/api/admin/debate-flow?stream_id=" + s2)
    gf1 = g1.get("data", {}).get("flow", [])
    gf2 = g2.get("data", {}).get("flow", [])
    ok("s1 flow 3 segs", len(gf1) == 3)
    ok("s2 flow 4 segs", len(gf2) == 4)
    if gf1: ok("s1 first='Opening Statement L'", gf1[0].get("name") == "Opening Statement L")
    if gf2: ok("s2 first='Opening All'", gf2[0].get("name") == "Opening All")

    # Control commands test
    print("\n  [Step] Control commands test...")
    actions = []
    # s1: start
    r = api("POST", "/api/admin/debate-flow/control",
            {"streamId": s1, "action": "start", "segmentIndex": 0}, auth=True)
    ok("s1 start", r.get("success"))
    # s2: start at segment 2
    r = api("POST", "/api/admin/debate-flow/control",
            {"streamId": s2, "action": "start", "segmentIndex": 2}, auth=True)
    ok("s2 start(idx=2)", r.get("success"))
    # s1: next
    r = api("POST", "/api/admin/debate-flow/control",
            {"streamId": s1, "action": "next", "segmentIndex": 1}, auth=True)
    ok("s1 next", r.get("success"))
    # s1: pause
    r = api("POST", "/api/admin/debate-flow/control",
            {"streamId": s1, "action": "pause", "segmentIndex": 1}, auth=True)
    ok("s1 pause", r.get("success"))
    # s2: next (independent)
    r = api("POST", "/api/admin/debate-flow/control",
            {"streamId": s2, "action": "next", "segmentIndex": 3}, auth=True)
    ok("s2 next(indep)", r.get("success"))
    # s1: resume
    r = api("POST", "/api/admin/debate-flow/control",
            {"streamId": s1, "action": "resume", "segmentIndex": 1}, auth=True)
    ok("s1 resume", r.get("success"))
    # s2: prev
    r = api("POST", "/api/admin/debate-flow/control",
            {"streamId": s2, "action": "prev", "segmentIndex": 2}, auth=True)
    ok("s2 prev", r.get("success"))
    # s1: reset
    r = api("POST", "/api/admin/debate-flow/control",
            {"streamId": s1, "action": "reset", "segmentIndex": 0}, auth=True)
    ok("s1 reset", r.get("success"))

    # Verify s2 was not reset by s1's reset
    g2f = api("GET", "/api/admin/debate-flow?stream_id=" + s2)
    ok("s2 flow still 4 segs after s1 reset",
       len(g2f.get("data", {}).get("flow", [])) == 4)

    print("\n  All control commands executed independently")

def test_103_api():
    """HTTP API part of WebSocket test: verify data isolation via REST"""
    print("\n" + "=" * 50)
    print("10.3 API Data Isolation (REST)")
    print("=" * 50)

    s1 = ensure("stream-1-test")
    s2 = ensure("stream-2-test")

    # Get initial votes
    v1 = api("GET", "/api/admin/votes?stream_id=" + s1)
    v2 = api("GET", "/api/admin/votes?stream_id=" + s2)
    lv1 = v1.get("data", {}).get("leftVotes", 0)
    rv1 = v1.get("data", {}).get("rightVotes", 0)
    lv2 = v2.get("data", {}).get("leftVotes", 0)
    rv2 = v2.get("data", {}).get("rightVotes", 0)

    # Modify s1 votes
    print("\n  [Step] Modify stream-1 votes...")
    api("PUT", "/api/admin/votes", {
        "action": "set", "leftVotes": 100, "rightVotes": 50, "streamId": s1
    }, auth=True)

    v1u = api("GET", "/api/admin/votes?stream_id=" + s1)
    v2u = api("GET", "/api/admin/votes?stream_id=" + s2)
    ok("s1 left=100", v1u.get("data", {}).get("leftVotes") == 100)
    ok("s1 right=50", v1u.get("data", {}).get("rightVotes") == 50)
    ok("s2 left unchanged", v2u.get("data", {}).get("leftVotes") == lv2,
       "expected " + str(lv2) + " got " + str(v2u.get("data", {}).get("leftVotes")))
    ok("s2 right unchanged", v2u.get("data", {}).get("rightVotes") == rv2,
       "expected " + str(rv2) + " got " + str(v2u.get("data", {}).get("rightVotes")))

    # Modify s2 votes
    print("\n  [Step] Modify stream-2 votes...")
    api("PUT", "/api/admin/votes", {
        "action": "set", "leftVotes": 200, "rightVotes": 100, "streamId": s2
    }, auth=True)

    v1uu = api("GET", "/api/admin/votes?stream_id=" + s1)
    v2uu = api("GET", "/api/admin/votes?stream_id=" + s2)
    ok("s1 left still 100", v1uu.get("data", {}).get("leftVotes") == 100)
    ok("s2 left=200", v2uu.get("data", {}).get("leftVotes") == 200)
    ok("s2 right=100", v2uu.get("data", {}).get("rightVotes") == 100)

    # Reset
    api("PUT", "/api/admin/votes", {"action": "reset", "streamId": s1}, auth=True)
    api("PUT", "/api/admin/votes", {"action": "reset", "streamId": s2}, auth=True)

if __name__ == "__main__":
    print("=" * 50)
    print("Multi-Stream HTTP API Test")
    print("Backend: " + BASE)
    print("Time: " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 50)

    # Login to get auth token
    login = api("POST", "/api/admin/login", {"username": "admin", "password": "admin123"})
    if login.get("success"):
        TOKEN = login.get("data", {}).get("token")
        print("Login OK, token: " + str(TOKEN)[:8] + "...")
    else:
        print("Login FAILED: " + str(login))
        # Continue anyway - GET endpoints are public

    # Check server
    try:
        ping = api("GET", "/api/admin/streams")
        if not ping.get("success"):
            print("Server unavailable: " + json.dumps(ping))
            sys.exit(1)
        print("Server OK (" + str(len(ping.get("data",{}).get("streams",[]))) + " streams)")
    except Exception as e:
        print("Cannot connect: " + str(e))
        sys.exit(1)

    try:
        test_101()
        test_102()
        test_103_api()
    except Exception as e:
        print("\nException: " + str(e))
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 50)
    total = p + f
    print("Results: " + str(p) + " PASS, " + str(f) + " FAIL, " + str(total) + " total")
    if f > 0:
        print("WARNING: Some tests FAILED")
    else:
        print("SUCCESS: All tests passed!")
    print("=" * 50)
