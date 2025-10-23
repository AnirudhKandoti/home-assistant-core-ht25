"""Utilities to fetch Google Tasks data and OAuth tokens for Home Assistant."""

# fetch_tasks.py
import os
import json
import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Paths
TOKEN_PATH = "/workspaces/core/config/token.json"
HA_WWW_PATH = "/workspaces/core/config/www"
TASKLIST_NAME = "My Tasks"
MAX_TASKS = 50

# Load credentials
if not os.path.exists(TOKEN_PATH):
    raise SystemExit(f"token.json not found at {TOKEN_PATH}; run get_tasks_oauth.py first")

creds = Credentials.from_authorized_user_file(TOKEN_PATH)

# Build service
service = build("tasks", "v1", credentials=creds)

# Pick tasklist
tasklists = service.tasklists().list(maxResults=100).execute().get("items", [])
selected_list_id = None
for tl in tasklists:
    if tl.get("title") == TASKLIST_NAME:
        selected_list_id = tl.get("id")
        break
if not selected_list_id and tasklists:
    selected_list_id = tasklists[0].get("id")
if not selected_list_id:
    raise SystemExit("No tasklist found")

# Fetch tasks 
tasks_res = (
    service.tasks()
    .list(tasklist=selected_list_id, maxResults=MAX_TASKS, showCompleted=False)
    .execute()
)
items = tasks_res.get("items", [])

# Transform
tasks_out = []
for it in items:
    tasks_out.append(
        {
            "id": it.get("id"),
            "title": it.get("title"),
            "notes": it.get("notes"),
            "status": it.get("status"),  # needsAction or completed
            "due": it.get("due"),        # RFC3339 timestamp or None
            "updated": it.get("updated"),
        }
    )

# Write JSON
os.makedirs(HA_WWW_PATH, exist_ok=True)
out_path = os.path.join(HA_WWW_PATH, "tasks.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(
        {
            "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
            "count": len(tasks_out),
            "tasks": tasks_out,
        },
        f,
        indent=2,
        ensure_ascii=False,
    )

print(f"Wrote {len(tasks_out)} tasks to {out_path}")