# Subtask 5: Document Known Limitations

**Status**: TO DO

## Description
Document known limitations for LINE integration, specifically edge cases that are not fully supported natively in our v1 application logic (e.g., group chats). 

## Documentation Details
1. **Current Scope Constraint**:
   - Building a merged contact identity cross-channel is explicitly noted as out of scope for the current v1 release. 
   - In particular, features like taking LINE Chatbots into public LINE groups and handling multi-actor dialogue in ONE thread isn't natively modeled natively without heavy structural changes.
2. **Action Required**:
   - Create a central known-limitations document or Wiki page for the Product and Tech teams.
   - List the technical constraints regarding Group Chat, Room contexts, and other unsupported payload types (e.g. `unsend` tracking).
   - This effectively scopes down scope creep and informs Customer Success to handle pilot accounts' expectations properly.
