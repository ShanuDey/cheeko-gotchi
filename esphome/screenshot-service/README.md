# Screenshot service

Renders one web page in headless Chromium (Playwright) and serves it as a
240x296 JPEG at `/frame.jpg` for the Cheeko Gotchi **Video** page. It lives apart
from `../wyoming-voice` so each stack updates on its own.

- The page is fixed by `TARGET_URL`, not taken from the request, so the service
  cannot fetch arbitrary URLs.
- Frames are sent with `Cache-Control: no-store` and no `Last-Modified`. Otherwise
  the device gets `304 Not Modified` and stalls.
- `MARGIN_PX` of black border keeps content out of the rounded screen corners.
- The default page is the built-in clock (`pages/clock.html`). Many public sites
  block headless browsers, so use your own pages or sites that allow it.
- One browser page serves one request at a time. A failed frame returns 502; the
  browser restarts if it died or after 5 failures in a row.
- Pages that need a login (an HA dashboard) are not supported yet.

## Deploy (Dockge)

`.github/workflows/screenshot-service.yml` builds this folder and pushes
`ghcr.io/shanudey/cheeko-screenshot`:

| Branch | Tag | Use |
|---|---|---|
| `main` | `latest` | stable |
| `dev` | `alpha` | testing before a release |
| any | `sha-<commit>` | pin an exact build |

It runs on pushes to `main` or `dev` that touch this folder, and from the
Actions tab. A manual run from a feature branch pushes only the `sha-` tag.

1. After the first run, set the package to **Public** (GitHub, Packages,
   `cheeko-screenshot`, Package settings). New packages are private; otherwise
   the host needs `docker login ghcr.io` with a `read:packages` token.
2. In Dockge, create a stack, paste `docker-compose.yaml`, and put
   `TARGET_URL=file:///app/pages/clock.html` in the `.env` box. Deploy.
3. In HA, set the device's **Video URL** to
   `http://<docker-host-ip>:28240/frame.jpg` (use the IP, not a `.local` name)
   and turn **Video Stream** on.

Use `:latest` for the always-on stack and `:alpha` to try changes.

## Run locally

`docker-compose.dev.yaml` adds `build: .` so Docker Desktop builds from this
folder. Do not paste it into Dockge.

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
- **`set TARGET_URL in .env`:** the `.env` box is empty or unsaved.
- **Connection refused after changing the port:** the three places above disagree.
