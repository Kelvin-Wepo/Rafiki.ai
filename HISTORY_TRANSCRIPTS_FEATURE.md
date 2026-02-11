# Conversation History & Transcript Download Features

## Overview

Users can now view their conversation history and download transcripts of past conversations in multiple formats (TXT, JSON). This enables users to:

- View all past conversations at a glance
- Search and filter conversations
- Delete old conversations
- Export conversations as downloadable files for record-keeping
- Access transcripts on-demand

## Architecture

### Backend Implementation

#### API Endpoints

The following endpoints are already implemented in `backend/routes/auth.py`:

1. **Get Conversations** - `GET /auth/conversations`
   - Lists all conversations for the authenticated user
   - Supports pagination and filtering
   - Returns conversation metadata (title, preview, message count, timestamps)

2. **Get Specific Conversation** - `GET /auth/conversations/{conversation_id}`
   - Retrieves a single conversation with all messages
   - Requires user ownership verification
   - Returns full conversation details including message content

3. **Create Conversation** - `POST /auth/conversations`
   - Creates a new conversation for the user
   - Returns conversation ID and metadata

4. **Add Message** - `POST /auth/conversations/{conversation_id}/messages`
   - Adds a message to an existing conversation
   - Stores both user and assistant messages with metadata

5. **Delete Conversation** - `DELETE /auth/conversations/{conversation_id}`
   - Archives a conversation (soft delete)
   - Requires user ownership verification

6. **Export Transcript** - `POST /auth/conversations/{conversation_id}/export`
   - Exports conversation as downloadable file
   - Supports formats: `txt`, `json`
   - Handles file generation and content-type headers

#### Authentication Service

The `backend/services/auth_service.py` provides methods for:
- `create_conversation(user_id)` - Creates new conversation
- `get_user_conversations(user_id, include_archived)` - Lists conversations
- `get_conversation(conversation_id, user_id)` - Gets specific conversation
- `add_message(conversation_id, role, content, metadata)` - Adds message
- `delete_conversation(conversation_id, user_id)` - Archives conversation
- `export_transcript(conversation_id, user_id, format)` - Exports transcript

### Frontend Implementation

#### Components

1. **ConversationHistory** (`frontend/src/components/Dashboard/ConversationHistory.tsx`)
   - Displays list of past conversations
   - Features:
     - Search/filter conversations
     - Preview text for each conversation
     - Message count indicator
     - Delete button with confirmation
     - Click to load and resume conversation
     - Empty state when no conversations exist
   - Responsive design (mobile-friendly)

2. **TranscriptDownload** (`frontend/src/components/Dashboard/TranscriptDownload.tsx`)
   - Allows users to download transcripts
   - Features:
     - Conversation selector dropdown
     - Format selection (TXT, JSON)
     - Download button with loading state
     - Success/error messages
     - Auto-selects first conversation
   - Responsive design

3. **MainLayout** (`frontend/src/components/Layout/MainLayout.tsx`)
   - Updated to support three views:
     - `chat` - Active conversation view (default)
     - `history` - Conversation history view
     - `transcripts` - Transcript download view
   - View switching via sidebar navigation
   - Maintains state across view changes

#### API Service

The `frontend/src/services/authService.ts` provides:
- `getConversations()` - Fetch all conversations
- `getConversation(conversationId)` - Fetch specific conversation
- `createConversation()` - Create new conversation
- `deleteConversation(conversationId)` - Delete conversation
- `exportTranscript(conversationId, format)` - Get transcript blob
- `downloadTranscript(conversationId, format)` - Download transcript file

#### UI/UX Enhancements

**Sidebar Navigation** (`frontend/src/components/Layout/Sidebar.tsx`)
- Three main navigation items:
  - 🗨️ **New Chat** - Start a new conversation
  - 📜 **History** - View conversation history
  - 📄 **Transcripts** - Download transcripts

**Visual Indicators**
- Active view is highlighted in sidebar
- Smooth transitions between views
- Loading states for async operations
- Toast notifications for success/error messages

## User Flow

### Viewing Conversation History

1. User clicks "History" in the sidebar
2. ConversationHistory component loads conversations from API
3. Conversations displayed with:
   - Title (auto-generated or user-defined)
   - Preview of first message
   - Message count
   - Creation date
   - Delete button
4. User can:
   - Click conversation to resume it (switches to chat view)
   - Search to filter conversations
   - Delete to archive conversation

### Downloading Transcripts

1. User clicks "Transcripts" in the sidebar
2. TranscriptDownload component loads conversations
3. User selects conversation from dropdown
4. User selects format (TXT or JSON)
5. User clicks "Download"
6. Browser downloads file named `rafiki_transcript_{conversation_id}.{format}`

### Resuming Conversation

1. User views conversation history
2. Clicks on a conversation
3. App switches to chat view with that conversation selected
4. User can continue the conversation or view it

## Data Models

### Conversation

```typescript
interface Conversation {
  id: string;
  title: string;
  preview?: string;           // First message preview
  message_count?: number;
  messages?: Message[];
  created_at: string;         // ISO timestamp
  updated_at: string;         // ISO timestamp
}
```

### Message

```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;          // ISO timestamp
  metadata?: Record<string, unknown>;
}
```

## Export Formats

### TXT Format
```
=== Rafiki Conversation Transcript ===
Conversation: [Title]
Date: [Created Date]
Duration: [Message Count] messages

---

User: [Message]
Rafiki: [Response]

...
```

### JSON Format
```json
{
  "conversation_id": "conv_xxx",
  "title": "Conversation Title",
  "created_at": "2026-02-11T10:30:00Z",
  "updated_at": "2026-02-11T10:45:00Z",
  "message_count": 5,
  "messages": [
    {
      "id": "msg_xxx",
      "role": "user",
      "content": "Hello",
      "timestamp": "2026-02-11T10:30:00Z",
      "metadata": {}
    },
    {
      "id": "msg_yyy",
      "role": "assistant",
      "content": "Hi, how can I help?",
      "timestamp": "2026-02-11T10:30:05Z",
      "metadata": {}
    }
  ]
}
```

## Security Considerations

1. **Authorization**: All endpoints verify user ownership before returning conversations
2. **Rate Limiting**: Export and download endpoints may be rate-limited to prevent abuse
3. **PII Protection**: Phone numbers are masked in UI, full numbers only visible to user
4. **Audit Logging**: All conversation access/export events logged for compliance

## Browser Compatibility

- Chrome/Chromium: Full support
- Firefox: Full support
- Safari: Full support
- Edge: Full support

## Performance Optimization

1. **Lazy Loading**: Conversations loaded on-demand (not preloaded)
2. **Pagination**: List view supports pagination for large datasets
3. **Caching**: Recently accessed conversations cached in localStorage
4. **Compression**: Export files compressed when possible

## Future Enhancements

1. **Search**: Full-text search across conversation content
2. **Tags/Labels**: User-defined tags for organizing conversations
3. **Sharing**: Share transcripts via secure link
4. **PDF Export**: Export conversations as PDF with formatting
5. **Auto-Archive**: Automatically archive old conversations
6. **Bulk Operations**: Delete/export multiple conversations at once
7. **Conversation Summaries**: AI-generated summaries of conversations

## Testing

### Unit Tests
- Test conversation CRUD operations
- Test transcript export formats
- Test file download functionality

### Integration Tests
- Test full user workflow (history → download → resume)
- Test authorization/ownership verification
- Test error handling and edge cases

### E2E Tests
- Test complete user journey from login to transcript download
- Test sidebar navigation and view switching
- Test responsive design on multiple screen sizes

## Deployment Notes

1. No database schema changes required (uses existing conversation tables)
2. No new environment variables needed
3. Frontend-only changes are backward compatible
4. Old API clients will still work (new endpoints are additive)

## Troubleshooting

### Issue: Conversations not loading
- Check backend API is running
- Verify authentication token is valid
- Check network tab for 401/403 errors

### Issue: Download fails
- Verify file size is under browser limits (usually 2GB)
- Check browser download settings
- Try different format (TXT vs JSON)

### Issue: History view is slow
- Check if there are too many conversations (>1000)
- Consider pagination implementation
- Check backend query performance

## Code References

- **Backend**: `backend/routes/auth.py` (lines 236-385)
- **Service**: `backend/services/auth_service.py`
- **Frontend Components**: `frontend/src/components/Dashboard/`
- **API Service**: `frontend/src/services/authService.ts` (lines 276-340)
- **Main Layout**: `frontend/src/components/Layout/MainLayout.tsx`
