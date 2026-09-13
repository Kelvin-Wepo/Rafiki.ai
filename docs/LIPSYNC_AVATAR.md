# Talking avatar lip-sync

Canvas mouth animation on the single Rafiki portrait (`frontend/src/assets/rafiki_avatar.png`). No viseme sprites and no GPU video models.

## Mouth-region coordinates

The mouth box is stored as **0–1 fractions of the source PNG** (`rafiki_avatar.png`, native **501×667**). The canvas draws that image with `object-fit: cover` into the circular frame, then maps the box through the same cover transform.

Live defaults (full lips on the native file):

| Field | Value |
|-------|-------|
| x | 0.388 |
| y | 0.43 |
| width | 0.222 |
| height | 0.092 |

A 274×328 preview measurement (x 92–160, y 152–191) is the same mouth in a *different* pixel frame. Copying those pixels as source fractions placed the deform box on the chin — do not do that if you swap the image. Re-measure on the PNG itself.

Playback sync: viseme cues **hold** until ~55ms before the next sound (they do not lerp across the whole cue). Open/close also follows the **playing audio waveform**, so the mouth stays locked to what you hear even if timestamps drift a little. Use ElevenLabs `alignment` (raw audio times), not `normalized_alignment`.

Clip bounds add **25%** padding around the mouth and grow with viseme scale so C/D (wide open) are not cut off.

Debug: pass `debug` (or `debugMouthBox`) to `<TalkingAvatar />` to draw a red rectangle on the mapped box. `/lipsync-demo` toggles this. The overlay is off by default in chat.

Tune in:

1. `<TalkingAvatar mouthRegion={{ x, y, width, height }} />`
2. Frontend env: `VITE_AVATAR_MOUTH_X`, `_Y`, `_WIDTH`, `_HEIGHT`
3. `frontend/src/components/avatar/lipsyncConfig.ts`
4. Backend env `AVATAR_MOUTH_REGION` as JSON, e.g.  
   `{"x":0.388,"y":0.43,"width":0.222,"height":0.092}`  

Open `/lipsync-demo` and toggle the red overlay while a clip plays.

## Viseme → mouth shape

Edit `frontend/src/components/avatar/visemeShapes.ts` (`VISEME_SHAPES`).

| Viseme | Typical sounds | `open` (vertical scale) | `width` (horizontal scale) |
|--------|----------------|-------------------------|----------------------------|
| X      | rest / silence | 1 (painted smile)       | 1                          |
| A      | p, b, m        | 0.78 closed             | ~0.96                      |
| B      | s, t, d, k     | slight open             | ~1.04                      |
| C      | e, i           | 1.34 wide               | 1.22                       |
| D      | a              | 1.48 wide open          | 1.18                       |
| E      | o              | rounded                 | ~0.92                      |
| F      | u, w           | medium, pursed          | ~0.80                      |
| G      | f, v           | teeth on lip            | ~1.02                      |
| H      | l              | tongue                  | 1                          |

Idle is `open = 1` so the portrait is not warped at rest. The painted mouth is already slightly open, so `open < 1` closes and `open > 1` opens further.

## Timeline generation

`backend/services/viseme_service.py` → `get_viseme_timeline(...)`.

Order:

1. ElevenLabs `POST /v1/text-to-speech/{voice_id}/with-timestamps` (preferred)
2. Rhubarb Lip Sync CLI if `rhubarb` or `RHUBARB_BIN` is on the server
3. PCM energy envelope so playback never waits on lip-sync

Chat TTS (`POST /api/agencies/chat*`) returns `audio_base64` and `viseme_timeline` together. If visemes are missing, the avatar pulses while audio plays.

## Demo

`/lipsync-demo` — play greeting / help / longer samples and check ~50–100ms tightness.
