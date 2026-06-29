"""Quick smoke test — run with: python3 test_api.py (server must be running on :8000)"""
import urllib.request, json, sys

BASE = "http://127.0.0.1:8000"

def req(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(BASE + path, data=data, method=method,
                               headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(r) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else None

def test():
    # create
    h = req("POST", "/habits", {"name": "Test habit"})
    assert h["name"] == "Test habit", h
    assert h["streak"] == 0, h
    hid = h["id"]
    print(f"  created habit id={hid}")

    # list
    habits = req("GET", "/habits")
    assert any(x["id"] == hid for x in habits)
    print(f"  list ok ({len(habits)} habits)")

    # toggle on
    t = req("POST", f"/habits/{hid}/toggle")
    assert t["completed_today"] == True
    print(f"  toggled on, streak={t['streak']}")

    # toggle off
    t = req("POST", f"/habits/{hid}/toggle")
    assert t["completed_today"] == False
    print(f"  toggled off, streak={t['streak']}")

    # rename
    updated = req("PATCH", f"/habits/{hid}", {"name": "Renamed"})
    assert updated["name"] == "Renamed"
    print("  rename ok")

    # delete
    r = urllib.request.Request(BASE + f"/habits/{hid}", method="DELETE")
    with urllib.request.urlopen(r) as resp:
        assert resp.status == 204
    print("  delete ok")

    habits2 = req("GET", "/habits")
    assert not any(x["id"] == hid for x in habits2)
    print("  confirmed deleted from list")
    print("\nAll tests passed.")

if __name__ == "__main__":
    test()
