# Display frame service

Renders one web page in headless Chromium (Playwright) and serves it as a
240x296 JPEG at `/frame.jpg` for the Cheeko Gotchi **Display Frame** page. It lives apart
from `../wyoming-voice` so each stack updates on its own.

- Presets are the `pages/*.html` files in the image. `/presets` lists their
  names and `/frame.jpg?page=<name>` renders one; the device shows them in the
  **Display Frame Source** select. To add one, drop a file in `pages/` (lowercase
  `a-z0-9_-` name) and rebuild the image.
- `/frame.jpg?url=<page>` renders a custom page (the device's **Display Frame URL**
  entity with source `Custom`). Only `http(s)` is
  accepted (bundled pages go through `?page=`). Set `ALLOWED_HOSTS` (comma separated hostnames) to stop the service
  being used as a proxy to other hosts on your network. Presets are not affected.
- With neither, the first bundled page (`clock`) is shown.
- Frames are sent with `Cache-Control: no-store` and no `Last-Modified`. Otherwise
  the device gets `304 Not Modified` and stalls.
- The page fills the whole 240x296 by default, so the rounded bezel hides what is in the
  four corners. A black border keeps content clear of them: set `MARGIN_PX` (0 to 20) in
  `.env` and redeploy. `/frame.jpg?margin=<px>` overrides it for one request.
- The default page is the built-in clock (`pages/clock.html`). Many public sites
  block headless browsers, so use your own pages or sites that allow it.
- One browser page serves one request at a time. A failed frame returns 502; the
  browser restarts if it died or after 5 failures in a row.
- Pages that need a login (an HA dashboard) work once you sign in through DevTools
  (below). The browser profile is kept in the `pw-data` volume, so the login
  survives restarts.

## DevTools

Off by default. To inspect what the service's browser renders, or to log in to a
page:

1. Set `DEVTOOLS=1` in the `.env` box and redeploy.
2. In Chrome on your PC open `chrome://inspect`, click **Configure**, add
   `<docker-host-ip>:28241`, then **inspect** the page under Remote Target.
3. For a login: open the page's URL as **Display Frame URL** (source `Custom`)
   so it loads, sign in through DevTools, and the session is saved.
4. Remove `DEVTOOLS` and redeploy when done.

Anyone on your LAN who can reach port 28241 controls the browser and any saved
login, so do not leave it on. Chromium only listens on localhost, so `server.py`
relays the port itself (the same job `remote-webview` gives to a `socat` container).

## Deploy

`.github/workflows/display-frame.yml` builds this folder and pushes
`ghcr.io/shanudey/display-frame`:

| Branch | Tag | Use |
|---|---|---|
| `main` | `latest` | stable |
| `dev` | `beta` | testing before a release |
| any other branch (manual run) | `alpha` | trying a change from a feature branch |
| any | `sha-<commit>` | pin an exact build |

It runs on pushes to `main` or `dev` that touch this folder, and from the
Actions tab. Every build also gets a `sha-` tag.

1. After the first run, set the package to **Public** (GitHub, Packages,
   `display-frame`, Package settings). New packages are private; otherwise
   the host needs `docker login ghcr.io` with a `read:packages` token.
2. On your Docker host, run `docker-compose.yaml` (`docker compose up -d`, or paste it
   into whatever manages your stacks). No `.env` is needed; see `.env.example` for the
   optional settings.
3. Set `display_frame_server: "http://<docker-host-ip>:28240"` in the ESPHome
   `secrets.yaml` (use the IP, not a `.local` name) and reflash. Change the
   page any time from HA with **Display Frame Source** (or **Display Frame URL**
   with `Custom`). Show the page with **Display Page** in HA or a long press of
   Volume Down.

Use `:latest` for the always-on stack, `:beta` for the dev branch and `:alpha` to try a feature branch.

## Run locally

`docker-compose.dev.yaml` adds `build: .` so Docker Desktop builds from this
folder. Use it only on a machine that has this source.

```bash
cp .env.example .env
docker compose -f docker-compose.yaml -f docker-compose.dev.yaml up -d --build
curl -o frame.jpg http://localhost:28240/frame.jpg
```

The local build is tagged like the published image, so `docker compose pull`
replaces it.

## Port

28240 is used on the host and inside the container, picked to avoid common
services. To change it, edit `ports:` in `docker-compose.yaml`, `PORT` in
`server.py` and `EXPOSE` in the `Dockerfile`, then rebuild.

## Troubleshooting

- **502:** `docker compose logs` shows the `frame failed:` reason.
- **Connection refused after changing the port:** the three places above disagree.
