---
description: Read ClickUp Epic using browser agent, generate detailed docs (TH/EN) per story, and save to specific directory.
---

1. **Extract Epic Stories (Browser)**
   - **Tool**: `browser_subagent`
   - **TaskName**: "Reading ClickUp Epic"
   - **TaskSummary**: "Read ClickUp Epic and its stories using a browser agent."
   - **RecordingName**: "clickup_epic_read"
   - **Task**: "Navigate to the ClickUp URL [URL]. First, read the Epic details. Then, open each associated story in the list. For EVERY single story: 1) Wait for the page to fully load. 2) Look for ANY 'Expand' or 'Show more' buttons (especially under the 'Detail / Description' section) and CLICK THEM to reveal the full hidden text. 3) Extract the EXACT, verbatim text for all sections including User Story, Detail / Description, Scope, Acceptance Criteria, and SUBTASKS. DO NOT summarize or paraphrase. Structure everything into detailed markdown documents (TH/EN) per story. Save the Epic summary and all story files into a new subdirectory `D:\\Work\\Meaw - Q\\ACE\\ACE-Planning\\Omnichat\\EPIC-[EPIC_ID]\\`. Name the files using the descriptive pattern `[TaskID]_[StoryID]_[Cleaned_Title].md` (e.g., `ACE-701_STORY-MKT-01_Marketplace_Channel_Onboarding_v1.md`). Ensure you log in or handle any popups if necessary."
   - **explanation**: "Using browser_subagent to visually extract Epic details directly from the ClickUp web interface, with explicit instructions to expand all hidden text and capture details verbatim. It also dynamically targets a specific Epic directory. Replace [URL] with the actual ClickUp URL from the user's request."

2. **Notify User**
   - **Tool**: `print`
   - **Instruction**: "Inform the user that the Epic has been processed using the browser agent and individual story files have been created/updated in `D:\\Work\\Meaw - Q\\ACE\\ACE-Planning\\Omnichat\\EPIC-[EPIC_ID]\\` following the expected naming conventions."
