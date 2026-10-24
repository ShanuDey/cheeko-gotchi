# Screenshot service

Turns one web page into a 240x296 JPEG for the Cheeko Gotchi **Video** page. It
runs headless Chromium (Playwright) in Docker and serves the page screenshot at
`/frame.jpg`. It lives apart from `../wyoming-voice` so each stack starts and
updates on its own.

The page is fixed by `TARGET_URL`, not taken from the request, so the service
cannot be used to fetch arbitrary URLs. Frames carry `Cache-Control: no-store`
and no `Last-Modified`, which avoids the device's 304 loop. A black border of
`MARGIN_PX` keeps content out of the rounded screen corners.

## Prebuilt image (Dockge, no build)

`.github/workflows/screenshot-service.yml` builds this folder on GitHub and
pushes `ghcr.io/shanudey/cheeko-screenshot`. Tags:

| Branch | Tag | Use |
|---|---|---|
| `main` | `latest` | stable |
| `dev` | `alpha` | testing before a release |
| any | `sha-<commit>` | pin an exact build |

It runs on pushes to `main` or `dev` that touch this folder, or by hand from the
Actions tab. Feature branches such as `esphome` publish nothing on push; a
manual run from one pushes only the `sha-` tag. Until the first merge to `dev`,
use local builds (`docker compose up -d --build`). In Dockge, use `:latest` for
the always-on deploy and `:alpha` to try changes.

1. After the first run, open GitHub, your profile, **Packages**, the
   `cheeko-screenshot` package, **Package settings**, and set visibility to
   **Public** (new packages are private). Otherwise the host needs
   `docker login ghcr.io` with a token that has `read:packages`.
2. In Dockge, create a stack and paste `docker-compose.yaml`; the `.env` box
   takes `TARGET_URL`. No other files are needed. **Deploy** pulls the image.

## Run (on the HA / Docker host)

```bash
cp .env.example .env     # then edit TARGET_URL
docker compose up -d --build
curl -o frame.jpg http://localhost:8080/frame.jpg   # open it to check
```

Then in HA set the device's **Video URL** to
`http://<docker-host-ip>:8080/frame.jpg` and turn **Video Stream** on.
Use the host's IP, not a `.local` name.

## Notes

- Tested with Docker Desktop and the built-in clock page on the device. If a
  request returns 502, check `docker compose logs`; the browser restarts itself
  after a failed frame.
- Frames come from one shared browser page, one request at a time.
- A page that needs a login (an HA dashboard) is not handled yet; it would need
  a stored session or token, kept in an untracked file.
