---
description: Read ClickUp Epic using API, generate detailed docs (TH/EN) per story, and save to specific directory.
---

1. **Extract Epic Stories (API)**
   - **Tool**: `run_command`
   - **TaskName**: "Fetching ClickUp Epic (API)"
   - **CommandLine**: "python3 /Users/peerapatpongnipakorn/Work/Planning/scripts/fetch_clickup_epic.py [URL/ID]"
   - **WaitMsBeforeAsync**: 5000
   - **SafeToAutoRun**: true
   - **explanation**: "Running the Python script to fetch Epic details via ClickUp API and generate markdown files. Replace [URL/ID] with the actual ClickUp URL or Task ID from the user's request."

2. **Notify User**
   - **Tool**: `print`
   - **Instruction**: "Inform the user that the Epic has been processed using the ClickUp API and individual story files have been created/updated in `/Users/peerapatpongnipakorn/Work/Planning/Omnichat/`."
