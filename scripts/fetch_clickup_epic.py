import requests
import json
import os
import re

API_KEY = os.environ.get("CLICKUP_API_KEY", "pk_54727970_0EXQ4PI25O71M1B7K2DBDFPTGESW0U98")
BASE_URL = "https://api.clickup.com/api/v2"
OUTPUT_DIR = "/Users/peerapatpongnipakorn/Work/Planning/Omnichat"

HEADERS = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}

def get_task_details(task_id):
    url = f"{BASE_URL}/task/{task_id}"
    params = {
        "include_subtasks": "true",
        "custom_task_ids": "true",
        "team_id": "25605274" # Extracted from URL, might be needed for custom IDs
    }
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code != 200:
        print(f"Error fetching task {task_id}: {response.status_code} {response.text}")
        return None
    return response.json()

def get_subtasks(task_id):
    # Depending on API, fetching task details with include_subtasks might be enough, 
    # but sometimes subtasks need a separate call if there are many or for specific filtering.
    # Let's try getting them from the task details first.
    # If not enough, we can use GET /task/{task_id}/task?subtasks=true
    pass # logic handled in main for now via 'subtasks' field in task or separate call if needed.

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")

def generate_markdown(story):
    task_id = story.get("custom_id") or story.get("id")
    title = story.get("name")
    status = story.get("status", {}).get("status", "UNKNOWN").upper()
    status_color = story.get("status", {}).get("color", "#808080")
    
    assignees_list = [u["username"] for u in story.get("assignees", [])]
    assignees_str = ", ".join(assignees_list) if assignees_list else "_Unassigned_"
    
    description = story.get("description", "") or "_No description provided._"
    
    # Custom Fields Table
    custom_fields_rows = []
    for cf in story.get("custom_fields", []):
        if "value" not in cf:
            continue
            
        val = cf["value"]
        # Handle different value types (dropdowns, labels, etc.)
        if "type_config" in cf and "options" in cf["type_config"]:
            options = cf["type_config"]["options"]
            selected_label = str(val)
            for opt in options:
                if "id" in opt and opt["id"] == val:
                    selected_label = opt.get("name") or opt.get("label")
                    break
                if "orderindex" in opt and opt["orderindex"] == val:
                    selected_label = opt.get("name") or opt.get("label")
                    break
            val = selected_label
        
        if isinstance(val, list):
             val = ", ".join([str(v) for v in val])
        
        custom_fields_rows.append(f"| {cf['name']} | {val} |")
    
    if custom_fields_rows:
        custom_fields_table = "| Field | Value |\n|---|---|\n" + "\n".join(custom_fields_rows)
    else:
        custom_fields_table = "_No custom fields_"

    # Subtasks Table
    subtasks_rows = []
    for sub in story.get("subtasks", []):
        sub_status = sub.get("status", {}).get("status", "UNKNOWN").upper()
        sub_name = sub['name']
        subtasks_rows.append(f"| {sub_name} | {sub_status} |")
    
    if subtasks_rows:
        subtasks_table = "| Subtask | Status |\n|---|---|\n" + "\n".join(subtasks_rows)
    else:
        subtasks_table = "_No subtasks_"
    
    # Technical Analysis
    text_lower = (description + " " + title).lower()
    diag_types = {
        "Sequence Diagram": ["sequence diagram", "sequence"],
        "ER Diagram": ["er diagram", "schema", "data model"],
        "API Spec": ["api", "endpoint"]
    }
    
    tech_rows = []
    for label, keywords in diag_types.items():
        present = "❌"
        for kw in keywords:
            if kw in text_lower:
                present = "✅"
                break
        tech_rows.append(f"| {label} | {present} |")
    
    tech_table = "| Requirement | Needed? |\n|---|---|\n" + "\n".join(tech_rows)

    # Beautified Markdown
    content = f"""# {task_id} {title}

> **Status:** `{status}` &nbsp; | &nbsp; **Assignees:** {assignees_str}

## 📝 Description
{description}

---

## 📋 Custom Fields
{custom_fields_table}

## 🏗️ Subtasks
{subtasks_table}

## 🔧 Technical Requirements
{tech_table}
"""
    return content

import sys

def main():
    if len(sys.argv) > 1:
        # User might pass full URL or just ID.
        arg = sys.argv[1]
        if "/t/" in arg:
            parts = arg.split("/t/")[1].split("/")
            # If path is like .../t/25605274/ACE-30
            if len(parts) >= 2:
                epic_id = parts[1] # Take the second part as task ID
            else:
                epic_id = parts[0] # Take the first part
            
            # Remove potential query params or fragments
            epic_id = epic_id.split("?")[0].split("#")[0]
        else:
            epic_id = arg
    else:
        epic_id = "ACE-31" # Default if no arg provided
    
    print(f"Fetching Epic {epic_id}...")
    epic_data = get_task_details(epic_id)
    
    if not epic_data:
        print("Failed to get Epic data.")
        return

    # In ClickUp, an "Epic" might just be a task, and "Stories" are its subtasks.
    stories = epic_data.get("subtasks", [])
    
    # If standard subtasks list is empty, try to fetch via subtasks endpoint (optional robustness)
    if not stories:
        print(f"No subtasks found in initial payload for {epic_id}. Checking via subtasks endpoint...")
        # Could implement specific subtask fetch here if needed, but 'include_subtasks=true' usually works.
        pass

    print(f"Found {len(stories)} stories.")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for story_summary in stories:
        story_id = story_summary["id"]
        print(f"Fetching full details for story {story_id}...")
        
        full_story = get_task_details(story_id)
        if full_story:
            md_content = generate_markdown(full_story)
            
            # Filename
            s_id = full_story.get("custom_id") or full_story.get("id")
            s_title = full_story.get("name")
            filename = f"{s_id}_{sanitize_filename(s_title)}.md"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md_content)
            
            print(f"Generated: {filepath}")

if __name__ == "__main__":
    main()
