# Habit Tracker

Minimal iOS habit tracker — create habits, check them off daily, see streaks.

## Structure

```
habit-tracker/
├── backend/          Python/FastAPI REST API + SQLite
│   ├── main.py
│   ├── test_api.py
│   └── habits.db     (created on first run)
└── ios/
    └── HabitTracker/ Drop these files into an Xcode project
        └── HabitTracker/
            ├── HabitTrackerApp.swift
            ├── ContentView.swift
            ├── HabitRowView.swift
            ├── HabitStore.swift
            ├── APIClient.swift
            └── Models.swift
```

## Backend Setup

**Requirements**: Python 3.9+, FastAPI, uvicorn

```bash
pip3 install fastapi uvicorn
cd habit-tracker/backend
uvicorn main:app --host 127.0.0.1 --port 8000
```

API docs available at http://127.0.0.1:8000/docs

### Endpoints

| Method | Path | Description |
|---|---|---|
| GET | /habits | List all habits with today's status + streak |
| POST | /habits | Create a habit `{"name": "..."}` |
| POST | /habits/{id}/toggle | Toggle today's completion |
| DELETE | /habits/{id} | Delete a habit |
| PATCH | /habits/{id} | Rename a habit `{"name": "..."}` |
| POST | /habits/reorder | Reorder `{"ordered_ids": [...]}` |

## iOS Setup

1. Open Xcode → File → New → Project → iOS App
2. Product Name: `HabitTracker`, Interface: **SwiftUI**, Language: **Swift**
3. Delete the auto-generated `ContentView.swift`
4. Drag all `.swift` files from `ios/HabitTracker/HabitTracker/` into the project
5. In `Info.plist`, add `NSAppTransportSecurity` → `NSAllowsLocalNetworking: YES` (for localhost HTTP)
   - Or add this to `Info.plist` directly:
     ```xml
     <key>NSAppTransportSecurity</key>
     <dict>
         <key>NSAllowsLocalNetworking</key>
         <true/>
     </dict>
     ```
6. Run the simulator — the app connects to `http://127.0.0.1:8000`

**Physical device**: Change `base` in `APIClient.swift` to your Mac's local IP (`http://192.168.x.x:8000`) and run uvicorn with `--host 0.0.0.0`.

## Running smoke tests

```bash
cd backend
python3 test_api.py
```

## P0 Feature Checklist

- [x] Create habit (name only, one tap)
- [x] Daily checklist view (all habits, today's state)
- [x] Toggle complete/incomplete (optimistic update)
- [x] Streak counter (consecutive days, resets on miss)
- [x] Delete habit (swipe-to-delete)
- [x] Backend persistence (SQLite, survives reinstall)

## P1 Features (implemented)

- [x] Drag-to-reorder habits
- [x] Rename habit (swipe left → Rename)
- [x] Empty state with illustration + copy
