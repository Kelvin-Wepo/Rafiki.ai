# User Guide: Conversation History & Transcript Downloads

## Quick Start

Conversation history and transcript download features are now fully integrated into the Rafiki AI Assistant. Here's how to use them.

## Accessing Your Features

### 1. View Conversation History

**Steps:**
1. Look at the left sidebar
2. Click on the **📜 History** icon
3. See all your past conversations listed

**In History View, you can:**
- 🔍 **Search** conversations by title
- 👀 **Preview** the first message of each conversation
- 📊 **See message count** for each conversation
- 📅 **Check creation date** for each conversation
- ▶️ **Resume** a conversation by clicking on it
- 🗑️ **Delete** old conversations with confirmation

### 2. Download Transcripts

**Steps:**
1. Click on the **📄 Transcripts** icon in the sidebar
2. Select a conversation from the dropdown
3. Choose your preferred format:
   - **TXT** - Plain text (easy to read)
   - **JSON** - Structured data (for processing)
4. Click **Download**
5. File saves as `rafiki_transcript_{id}.{format}`

**When you'd want to download:**
- Keep records for compliance/audit
- Share with colleagues
- Analyze conversation data
- Backup important discussions
- Import into other systems (JSON)

### 3. Start New Chat

**Always available:**
1. Click the **💬 New Chat** icon in the sidebar
2. Begin a fresh conversation
3. Your previous conversations remain in history

## Understanding the Views

### Chat View (Default)
- See the talking avatar (Rafiki)
- Interact with the assistant in real-time
- Send voice or text messages
- Get instant responses

### History View
```
Your Conversations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 KRA PIN Recovery - 5 messages - Feb 11
   Preview: "I need help recovering my KRA PIN..."
   
📌 Passport Appointment Booking - 8 messages - Feb 10
   Preview: "Can I book a passport appointment online?"
   
📌 Tax Compliance Check - 3 messages - Feb 9
   Preview: "What documents do I need for my tax return?"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Transcripts View
```
Select a Conversation to Download
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Conversation: [KRA PIN Recovery ▼]
Format: [TXT ▼]
[Download] [Clear]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## File Formats Explained

### TXT Format (Human-Readable)
```
=== Rafiki Conversation Transcript ===
Conversation: KRA PIN Recovery
Date: February 11, 2026
Duration: 5 messages

---

User: I need help recovering my KRA PIN
Rafiki: I can help you with KRA PIN recovery. Let me get the requirements...

User: What documents do I need?
Rafiki: You'll need your ID and proof of registration...

...
```
**Best for:** Reading, sharing with non-technical people, printing

### JSON Format (Structured Data)
```json
{
  "conversation_id": "conv_abc123",
  "title": "KRA PIN Recovery",
  "created_at": "2026-02-11T10:30:00Z",
  "updated_at": "2026-02-11T10:45:00Z",
  "message_count": 5,
  "messages": [
    {
      "role": "user",
      "content": "I need help recovering my KRA PIN",
      "timestamp": "2026-02-11T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "I can help you with KRA PIN recovery...",
      "timestamp": "2026-02-11T10:30:05Z"
    }
  ]
}
```
**Best for:** Data processing, API integration, backup, analysis

## Tips & Tricks

### 💡 Pro Tips

1. **Organize with Titles**: The first few messages of a conversation create the title. Be specific!
2. **Regular Downloads**: Download important conversations regularly for records
3. **Use Search**: Can't find a conversation? Use the search box in History view
4. **Archive Old Conversations**: Delete conversations you no longer need to keep history clean
5. **Compare Formats**: Download same conversation in both TXT and JSON to see the difference

### 🔒 Security Notes

- Your phone number is **masked** in the UI (e.g., +254...3456)
- Conversations are **encrypted** in transit
- Only **you** can access your conversations
- Downloads are secure and private to your computer
- No conversations are shared with anyone

### 📱 Mobile Access

- Works on phones and tablets
- Sidebar collapses to icons on small screens
- Swipe to open/close sidebar on mobile
- Download works the same way
- Touch-friendly buttons

## Common Questions

### Q: How long are conversations stored?
**A:** Indefinitely until you delete them. You can keep important conversations forever.

### Q: Can I edit a conversation after saving?
**A:** Not directly, but you can download and modify the TXT/JSON files yourself.

### Q: What happens when I delete a conversation?
**A:** It's archived (soft deleted). You can ask us to permanently delete it if needed.

### Q: Can I download all conversations at once?
**A:** Currently, one at a time. Download multiple transcripts separately if needed.

### Q: Is there a limit to conversation history?
**A:** No hard limit, but performance may slow with extremely large histories (1000+).

### Q: Can I share my transcript with someone?
**A:** Yes! Download it and send the file via email or messaging app.

### Q: What if the download fails?
**A:** Try a different format (TXT instead of JSON). Check your internet connection and browser download settings.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `H` | Go to History view |
| `T` | Go to Transcripts view |
| `C` | Go to Chat view |
| `N` | New Chat |
| `Esc` | Close sidebar (mobile) |

## What's Next?

Keep an eye out for upcoming features:
- 🔐 Password-protected transcripts
- 📊 Conversation analytics and statistics
- 📤 Email transcripts directly
- 🏷️ Tag and organize conversations
- 🔗 Share via secure link
- 📥 Import previous transcripts

## Need Help?

- Check the **Help** icon in the sidebar
- Review the [technical documentation](./HISTORY_TRANSCRIPTS_FEATURE.md)
- Contact support for issues

---

**Happy chatting! 🎉**

*Your conversation history is your knowledge base. Keep what matters, delete what doesn't!*
