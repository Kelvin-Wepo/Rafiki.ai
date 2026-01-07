# Avatar Personality System Integration Guide

## Overview

The Rafiki avatar system now includes personality presets that control animation behavior, making the avatar more lively and expressive. This guide explains how to integrate and use these features.

## Personality Presets

Four distinct personalities are available:

### 1. Friendly (Default)
- **Expression Scale**: 1.2 - Moderate expressions
- **Head Movement**: Enabled - Natural head motion
- **Preprocessing**: Full - Maximum visual quality
- **Use Case**: General conversation, welcoming users

### 2. Professional
- **Expression Scale**: 0.8 - Subdued expressions
- **Head Movement**: Disabled - Minimal movement
- **Preprocessing**: Crop - Focus on face
- **Use Case**: Business meetings, formal communication

### 3. Excited
- **Expression Scale**: 1.5 - Exaggerated expressions
- **Head Movement**: Enabled - Active movement
- **Preprocessing**: Full - Maximum visual quality
- **Use Case**: Celebrations, positive news, energetic content

### 4. Calm
- **Expression Scale**: 0.6 - Subtle expressions
- **Head Movement**: Disabled - Stable pose
- **Preprocessing**: Crop - Focus on face
- **Use Case**: Meditation guides, serious topics, soothing content

## Backend Integration

### Setting Personality Globally

```python
from services.sadtalker_service import SadTalkerService

service = SadTalkerService()

# Change personality for all subsequent generations
service.set_personality('excited')
```

### Generating Video with Personality

```python
# Method 1: Use global personality setting
service.set_personality('professional')
video_path, error = await service.text_to_video(
    text="Welcome to our business meeting.",
    avatar_id="rafiki_avatar"
)

# Method 2: One-time personality (doesn't change global setting)
video_path, error = await service.generate_with_personality(
    text="Congratulations on your achievement!",
    personality="excited",
    avatar_id="rafiki_avatar"
)
```

## API Endpoints

### GET /api/avatar/personality

Get current personality setting:

```bash
curl http://localhost:8000/api/avatar/personality
```

Response:
```json
{
  "success": true,
  "personality": "friendly",
  "available_personalities": ["friendly", "professional", "excited", "calm"]
}
```

### POST /api/avatar/personality

Change personality:

```bash
curl -X POST http://localhost:8000/api/avatar/personality \
  -F "personality=excited"
```

Response:
```json
{
  "success": true,
  "personality": "excited",
  "message": "Avatar personality set to 'excited'"
}
```

### POST /api/avatar/text-to-video

Generate video with personality:

```bash
curl -X POST http://localhost:8000/api/avatar/text-to-video \
  -F "text=Hello! How can I help you today?" \
  -F "avatar_id=rafiki_avatar" \
  -F "personality=friendly" \
  -F "use_elevenlabs=true"
```

## Frontend Integration

### React Hook Usage

```typescript
import { useSadTalker } from '@/hooks/useSadTalker';

function AvatarComponent() {
  const { 
    generateFromText, 
    currentVideoUrl, 
    isLoading 
  } = useSadTalker();

  const handleSpeak = async (text: string, mood: string) => {
    await generateFromText({
      text,
      personality: mood,
      avatarId: 'rafiki_avatar'
    });
  };

  return (
    <div>
      <button onClick={() => handleSpeak("Welcome!", "friendly")}>
        Friendly Greeting
      </button>
      <button onClick={() => handleSpeak("Great news!", "excited")}>
        Excited Message
      </button>
      {currentVideoUrl && <video src={currentVideoUrl} autoPlay />}
    </div>
  );
}
```

### Updating the Hook

Add personality parameter to `useSadTalker.ts`:

```typescript
interface GenerateOptions {
  text: string;
  avatarId?: string;
  personality?: 'friendly' | 'professional' | 'excited' | 'calm';
  useElevenlabs?: boolean;
}

const generateFromText = async ({
  text,
  avatarId = 'rafiki_avatar',
  personality = 'friendly',
  useElevenlabs = true
}: GenerateOptions) => {
  const formData = new FormData();
  formData.append('text', text);
  formData.append('avatar_id', avatarId);
  formData.append('personality', personality);
  formData.append('use_elevenlabs', String(useElevenlabs));

  const response = await fetch('/api/avatar/text-to-video', {
    method: 'POST',
    body: formData
  });
  
  // ... handle response
};
```

## Advanced Features

### Enhanced Video Quality

All personalities use `gfpgan` face enhancement by default for better quality. This can be disabled if needed:

```python
service.settings['enhancer'] = None  # Disable enhancement
```

### Natural Eye Blinking

Reference videos are used for natural eye blinking animations. The system automatically uses example videos from SadTalker if available.

### Custom Personality Presets

Create custom presets by extending `PERSONALITY_PRESETS`:

```python
PERSONALITY_PRESETS['energetic'] = {
    'expression_scale': 1.8,
    'still_mode': False,
    'preprocess': 'full',
    'enhancer': 'gfpgan',
    'ref_eyeblink': DEFAULT_REF_EYEBLINK
}
```

## Context-Aware Personality Selection

Implement intelligent personality switching based on conversation context:

```python
def select_personality(message_content: str, intent: str) -> str:
    """Select appropriate personality based on context"""
    
    # Excited for positive intents
    if intent in ['booking_confirmed', 'appointment_success']:
        return 'excited'
    
    # Professional for business inquiries
    if intent in ['service_info', 'pricing_info']:
        return 'professional'
    
    # Calm for sensitive topics
    if any(word in message_content.lower() for word in ['cancel', 'problem', 'issue']):
        return 'calm'
    
    # Default friendly
    return 'friendly'

# Usage with Gemini responses
gemini_response = await gemini_service.get_response(user_message)
intent = detect_intent(user_message)
personality = select_personality(gemini_response, intent)

video_path, error = await sadtalker_service.generate_with_personality(
    text=gemini_response,
    personality=personality,
    avatar_id='rafiki_avatar'
)
```

## Performance Considerations

1. **Caching**: Personality settings don't affect caching - cache by text content
2. **Generation Time**: Expression scale affects processing time slightly
3. **Enhancement**: Face enhancement adds 1-2 seconds per video

## Testing

Run the personality test script:

```bash
cd backend
python test_personality.py
```

This verifies:
- Personality switching
- Settings persistence
- Available personalities
- Invalid input handling

## Troubleshooting

### Personality Not Changing

Check that settings are being applied:
```python
print(service.current_personality)
print(service.settings)
```

### Video Quality Issues

Enable enhancement if disabled:
```python
service.settings['enhancer'] = 'gfpgan'
```

### Reference Videos Not Loading

Verify SadTalker path:
```python
from pathlib import Path
ref_video_path = Path("../SadTalker/examples/ref_video")
print(f"Exists: {ref_video_path.exists()}")
print(f"Videos: {list(ref_video_path.glob('*.mp4'))}")
```

## Next Steps

1. **Add More Personalities**: Create custom presets for your use case
2. **Context Detection**: Implement automatic personality selection
3. **User Preferences**: Allow users to choose their preferred personality
4. **Analytics**: Track which personalities perform best
