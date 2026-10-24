# Voice assistant

The device is a push-to-talk microphone and speaker for HA's Assist pipeline
(speech to text, conversation agent, text to speech). By default it is push-to-talk.
Turn on the **Wake Word Mode** switch in HA to use a wake word as well: the device
runs ESPHome's on-device `micro_wake_word` (models `okay_nabu` and `hey_jarvis`) and
only talks to HA once it hears one. Pick the active model in the device's **Wake word**
select in HA. Holding Volume Up still works in both modes. The switch survives reboots.
A green dot at the top center of the screen shows whenever the mic is open (wake word
listening or recording a request). It is not drawn on the WebView page.
HA's openWakeWord add-on is not used: HA only offers a wake word for an ESPHome device
from the models the device itself reports.

## Use it

1. In HA, open the device page and set its **Assist pipeline** to the one you
   want (an LLM conversation agent gives open-ended chat).
2. Hold **Volume Up** for about 1 second. A short press still raises the volume.
   Hold again while it is running to cancel.
3. The face shows the state: wide eyes with pulsing rings (listening), eyes
   glancing aside with three dots (thinking), then the talking mouth while the
   reply plays. A red `voice error` caption appears for 3 s if the pipeline fails.

Replies play through the **Speaker** media player, so the volume buttons control
them.

## Tuning

Tune `mic_gain` (under `audio_adc`) and `noise_suppression_level`,
`auto_gain` and `volume_multiplier` (under `voice_assistant`) if speech is
quiet or misheard. The mic also hears the speaker, so interrupting a reply is
unreliable.

See [troubleshooting.md](troubleshooting.md) if the assistant does nothing.
