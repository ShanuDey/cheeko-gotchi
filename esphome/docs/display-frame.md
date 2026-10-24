# Display Frame (JPEG snapshots)

ESPHome has no video player, so the **Display Frame** page shows JPEG snapshots fetched
one after another over HTTP (a few frames per second, no audio).

1. Serve JPEG frames already scaled to 240x296. The device only decodes; it
   does not resize. Leave a safe margin for the rounded corners (see
   [display-pages.md](display-pages.md)).
   [display-frame/](../display-frame/README.md) does this: it renders a
   page (a built-in clock by default) in headless Chromium and serves it at
   `http://<docker-host-ip>:28240/frame.jpg`.
2. Put the service address in your secrets as `display_frame_server`
   (`http://<docker-host-ip>:28240`, use the IP) and the default page as
   `display_frame_url`. In HA, **Display Frame Source** picks a page bundled with the service
   (the list comes from the service a few seconds after boot) or `Custom`,
   which renders whatever **Display Frame URL** holds (sent as `?url=`). No reflash needed.
3. Long press Volume Down until the Display Frame page shows (the order is Face,
   Clock, Message, Display Frame, WebView), or set **Display Page** to Display Frame
   in HA. Fetching runs only while that page is showing, so choosing another page
   stops it.

The page shows "Loading..." until the first frame decodes. After 3 failed
fetches in a row (server down, wrong port, malformed or empty URL) it shows
"No frame" with "check Frame URL" (or `display_frame_server`). The device keeps retrying every second and the
picture returns once the server answers. Touch does nothing on this page; change
page with Volume Down (long press) or **Display Page** in HA.

## Server requirements

The server must not send `Last-Modified` or allow caching (send
`Cache-Control: no-store`). Otherwise the device sends `If-Modified-Since`,
gets `304 Not Modified`, and the log fills with `HTTP Request failed; Code: 304`.
The page select is not restored on boot, so a reboot lands on Face.

## Implementation note

The next download is started by the `fetch_next` script, never from inside
`on_download_finished` or `on_error`. ESPHome tears down the connection right
after those callbacks, so a download started inside them is aborted and the
image is released (frozen frame, then a black screen).
