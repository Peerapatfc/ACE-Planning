# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

Planning and specification repository for **Omnichat Unified Inbox** (ACE project) by Zimple Digital. Contains product documentation, user stories, and ClickUp-exported markdown files. No application code lives here — implementation is in separate repos.

## Tooling

### ClickUp MCP Server (primary)
ClickUp MCP server is available — use it directly to read and manage tasks without leaving Claude Code.

Common operations:
- **Get task details:** `clickup_get_task` with task ID (e.g. `ACE-1098`)
- **Search tasks:** `clickup_search` or `clickup_filter_tasks`
- **Get workspace hierarchy:** `clickup_get_workspace_hierarchy` to browse spaces/folders/lists
- **Get task comments:** `clickup_get_task_comments`
- **Update task:** `clickup_update_task`
- **Create task comment:** `clickup_create_task_comment`

Workspace team ID: `25605274`

### Browser-based extraction (fallback)
Follow `workflows/read_clickup_details.md` — uses `browser_subagent` to extract full verbatim descriptions including collapsed sections the API may miss.

## Directory Structure

```
Omnichat/
  EPIC-ACE-{ID}/       # One folder per epic
    {ACE-ID}_{STORY-ID}_{Title}.md    # Canonical story file
    STORY-{ID}_{Title}-{timestamp}.md # Older/draft snapshots
Dark mode.tokens.json  # Figma design token export (W3C format)
Light mode.tokens.json
workflows/read_clickup_details.md
```

## Epics Overview

| Epic | Area | Phase | Notes |
|------|------|-------|-------|
| ACE-30 | Marketplace Baseline | Foundation | Multi-tenant channel/credential schema |
| ACE-31 | Social Connectors | Foundation | LINE, Meta, Instagram |
| ACE-32 | Marketplace Connectors | Foundation | Shopee, Lazada, TikTok |
| ACE-33 | Communication Patterns | Foundation | Polling framework + state management |
| ACE-1098 | Inbox Core UI | MVP | Conversation list, timeline, composer |
| ACE-1365 | Contact Profile | MVP | Customer context, order history |
| ACE-1439 | Search/Filter/Sort | MVP | Unified search, filters, saved views |
| ACE-1472 | Commerce Context | MVP | Order details, unified history |
| ACE-1610 | RBAC | MVP | Admin/Supervisor/Agent 3-tier roles |
| ACE-1614 | Settings & Config | MVP | Workspace settings, business hours, members |
| ACE-1618 | SLA Management | MVP | SLA rules, overdue tracking |
| ACE-1970 | Login Security | MVP | MFA, sessions, account lock, field encryption |

## Domain Architecture

**Core data model** (established in Foundation epics):
- `Tenant` → many `ChannelAccount` (one per external account, e.g. LINE OA)
- `ChannelAccount` → `ChannelConnection` (tracks connect state, last error, timestamps)
- `ChannelCredentialRef` (credential reference only — no raw tokens stored in the account model)
- Channels: `line`, `facebook`, `instagram`, `tiktok`, `shopee`, `lazada`

**Key design constraints** carried across all epics:
- Multi-tenant from day one — every schema assumes `tenant_id` isolation
- Channel abstraction is vendor-neutral — schema must accommodate adding new channels without migration
- Credentials stored by reference (separate service/vault), not inline
- RBAC (ACE-1610) gates all inbox operations — stories reference permission checks against Admin/Supervisor/Agent roles

## Story Analysis Workflow

When analyzing or estimating a story, always cross-reference the implementation repo at
`D:\Work\Meaw - Q\ACE\ace` to identify what already exists vs what needs building.

Per epic, two companion files are created alongside story files:
- `epic-explanation.md` — Thai human-friendly narrative of the whole epic
- `story-task-breakdown.md` — task breakdown per story with 🔧 (fix existing) or (no icon = new) markers

## Document Conventions

**File naming:** `{ACE-ID}_{STORY-ID}_{Snake_Case_Title}.md`
Example: `ACE-1611_STORY-RBAC-01_Diagrams_and_API_Docs.md`

**Story structure:** Each `.md` contains: Status, Assignees, User Story, Acceptance Criteria (BDD Given/When/Then), UI/UX Notes, Technical Notes, API surface, Data model, Dependencies, QA edge cases.

**Language:** Bilingual — Thai for narrative/context, English for acceptance criteria and technical specs. Both appear in the same file.

## Design Tokens

`Dark mode.tokens.json` and `Light mode.tokens.json` are W3C design token exports from Figma. Use these as the source of truth for color, typography, and spacing values when documenting UI stories or reviewing implementation against design.
