# WebView page

The **WebView** page shows an HA dashboard (or any web page) rendered by the
Remote WebView server ([remote-webview/](../remote-webview/)) and streamed to the
device as JPEG tiles. Taps on the screen are forwarded to the page. The client is
the `remote_webview` component, a patched copy of strange-v's RemoteWebViewClient
(see [components/remote_webview/README.md](../components/remote_webview/README.md)).

- **Server and page:** set `webview_server` (`host:port`, no `http://`, use the IP)
  and `webview_url` in your secrets. See [install.md](install.md).
- **Change the page without reflashing:** the **WebView URL** text entity in HA.
  It is not kept across reboots; `webview_url` is the default.
- **Open it:** long press Volume Down until the WebView page shows, or set
  **Display Page** to WebView in HA.
- **Screen sharing:** the voice assistant, audio, the volume popup and firmware
  updates take the screen back from the page while they run, then it repaints.
- **Flipped page:** the display's own `mirror_x` already orients every page. The
  **WebView Flip X** switch (off after every reboot) is a debugging aid if only
  this page ever looks mirrored.
- **Touch:** the touch panel is rotated against the display; the calibration in
  `cgotchi.yaml` is a first guess from [SKILL.md](../../SKILL.md) section 5. Tune it
  with the VERBOSE touch log if taps land off target.
