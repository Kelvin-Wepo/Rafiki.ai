# Voice Detection Debugging Guide

## Common Voice Detection Issues and Solutions

### Issue 1: "No speech detected" Error

**Symptoms:**
- App shows "No speech detected" message even when you're speaking
- Microphone level indicator shows movement but audio isn't recognized

**Causes & Solutions:**

1. **Microphone not working properly**
   - Open Browser DevTools (F12)
   - Go to Console
   - You should see: `🎤 Voice detected - Level: XX` when speaking
   - If not, your microphone isn't capturing audio

2. **Browser doesn't have microphone permission**
   - Check browser settings for this website
   - Ensure microphone access is "Allowed"
   - Try incognito/private mode to test permissions
   - Check console for: `Microphone access denied`

3. **Microphone volume too low**
   - Check system audio settings
   - Test microphone in another app first (Skype, Discord, etc.)
   - Try speaking closer to the microphone
   - Disable echo cancellation temporarily if available

4. **Audio quality issues**
   - Too much background noise
   - Use a quieter environment
   - Try a different microphone
   - Ensure audio sample rate is 16kHz or higher

### Issue 2: Speech Recognition Service Error

**Symptoms:**
- Error message: "Speech recognition service error"
- Works locally but fails on production

**Causes & Solutions:**

1. **Network connectivity issue**
   - Check internet connection
   - Google Speech Recognition API requires internet
   - Check browser console for network errors

2. **Google Speech Recognition API limits**
   - Free tier has rate limits
   - Implement request caching/throttling
   - Consider paid alternative (Azure, AWS)

### Issue 3: Empty Audio Data

**Symptoms:**
- Backend receives empty audio data
- Error: "Audio data is empty after decoding"

**Causes & Solutions:**

1. **Audio not being recorded**
   - Check if Web Speech API recognized speech
   - Verify `finalTranscript` has content in console
   - Audio may have been too short or silent

2. **Base64 encoding issue**
   - Verify audio is properly encoded to base64
   - Check for corrupt audio data
   - Verify MIME type matches (audio/wav, audio/webm, etc.)

## Frontend Debugging Steps

### Step 1: Check Browser Console

Open DevTools (F12) and look for:
- ✅ `Microphone access granted` - Good, permissions OK
- ✅ `Audio tracks: [...]` - Microphone is connected
- ✅ `🎤 Voice detected - Level: XX` - Speaking is detected
- ❌ `Audio monitoring error` - Microphone issue
- ❌ `Microphone access denied` - Permission issue

### Step 2: Check Audio Levels

While speaking:
- You should see the audio level indicator move
- Look for console logs with voice detection level
- Levels below 30 are very quiet
- Levels above 100 indicate clear speech

### Step 3: Test Individual Components

```javascript
// Test 1: Microphone access
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => console.log("✅ Microphone OK", stream))
  .catch(err => console.error("❌ Microphone Error:", err));

// Test 2: Speech Recognition support
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) console.log("✅ Speech Recognition supported");
else console.log("❌ Speech Recognition not supported");

// Test 3: Test voice hook
// Open browser console and check for debug messages
```

## Backend Debugging Steps

### Step 1: Check Voice Service Initialization

Look for logs:
```
Speech recognizer initialized with optimized settings
TTS engine initialized
```

If you see warnings, the service didn't initialize fully.

### Step 2: Monitor Transcription Process

When sending audio, check logs for:
```
Received audio data: XXXX bytes in wav format
Audio written to temporary file: /tmp/...
Audio loaded, attempting recognition...
Transcribed: "Your speech here"...
```

If any step is missing, that's where the issue is.

### Step 3: Check Audio File Quality

Enable debug logging in `voice_service.py`:

```python
# Add after audio bytes are written
import wave
with wave.open(temp_path, 'rb') as wav_file:
    logger.info(f"Audio: {wav_file.getnchannels()} channels, {wav_file.getframerate()} Hz, {wav_file.getnframes()} frames")
```

Look for:
- 1-2 channels (mono or stereo)
- 16000 Hz sample rate (standard)
- Sufficient frames (more than a few thousand)

## Quickstart: Enable Debug Mode

### Frontend
Add this to browser console when testing:
```javascript
// Monitor all speech recognition events
const hook = useVoiceConversation();
// All events will now log to console
```

### Backend
Set environment variable:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

Then restart the app and check logs.

## Recommended Test Flow

1. **Before coding:** Test microphone works in another app
2. **Frontend:** Open console and verify audio levels while speaking
3. **Send audio:** Send test audio and check backend logs
4. **Check response:** Verify transcribed text in response

## Audio Format Requirements

- **Format:** WAV or WebM
- **Sample Rate:** 16000 Hz (16 kHz)
- **Channels:** 1 (mono) or 2 (stereo)
- **Bit Depth:** 16-bit
- **Duration:** 0.5 - 30 seconds

## If Nothing Works

1. Check browser developer tools console for errors
2. Test microphone in system settings
3. Restart the app completely
4. Try a different browser (Chrome, Firefox, Edge)
5. Check firewall/VPN isn't blocking audio
6. Try localhost instead of network IP (if applicable)
7. Check backend logs for detailed error messages
8. Verify all dependencies are installed: `python -m pip install speech_recognition pyttsx3`
