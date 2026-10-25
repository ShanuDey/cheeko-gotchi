# Home Assistant entities

What the device page in HA shows.

| Entity | Type | Purpose |
|---|---|---|
| Backlight | light | Dimmable LCD backlight. |
| Speaker | media player | Play audio and TTS; the volume buttons control it. |
| Display Page | select | Face, Clock, Message, Display Frame, WebView. |
| Display Frame Source | select | Page bundled with the display-frame service, or Custom. |
| Display Frame URL | text | Page rendered when the source is Custom. |
| WebView URL | text | Page shown on the WebView page. |
| WebView Current URL | text sensor | URL the WebView is on. |
| WebView Flip X | switch | Debug mirror for the WebView page. |
| Clock Format | select | 12 or 24 hour. |
| Face Expression | select | Happy, Sad, Sleepy, Surprised, Angry, Laughing, Confused, Love, Wink. |
| Face Color | light | Color picker for the face only. |
| Face Color Preset | select | Named face colors, or Custom. |
| Message Title / Message Body | text | Content of the Message page. |
| Wake Word Mode | switch | On-device wake word, see [voice-assistant.md](voice-assistant.md). |
| Mic Level | sensor | Loudness in dB. |
| Volume Up / Volume Down | binary sensor | The hardware buttons. |

Mic Level only updates while something else is capturing audio (it is passive).
The power latch (GPIO 2) and speaker amp (GPIO 4) switches are hidden on purpose.
