# Alfred Web Client

A single self-contained `index.html` that replaces the Python microphone client with a
browser-based push-to-talk voice interface. No build step, no dependencies — open the file
and go.

## Run

Just open [index.html](index.html) in a modern browser (Chrome / Edge / Firefox), by
double-clicking it or dragging it into a tab. Nothing hosts the client itself.

**Microphone permission tip:** the client acquires the mic once and keeps it for the
session, so you are only prompted on the first press. Browsers do **not** persist the mic
grant for `file://` pages, so a page reload prompts again. To be prompted only once ever,
serve the folder from a stable origin instead, e.g. `python -m http.server 5500` in this
directory, then open `http://localhost:5500`.

## Configuring the endpoints (the ".env" for the browser)

A static page can't read a real `.env` file, so the equivalent is a small sibling
**`config.js`** loaded at startup. Copy [config.example.js](config.example.js) to `config.js`
and set your addresses:

```js
window.ALFRED_CONFIG = {
  api: "http://server_ip_address:8000", // local-assistant-server
  lifecycle: "http://server_ip_address:9000", // server-lifecycle-manager
};
```

`config.js` is git-ignored (machine-specific), mirroring the `.env` / `.env.example`
convention. Resolution precedence, highest first:

1. URL query param — `index.html?api=http://host:8000&lifecycle=http://host:9000`
2. `window.ALFRED_CONFIG` from `config.js`
3. built-in defaults (`http://192.168.0.219:8000` / `:9000`)

If `config.js` is absent the page still loads and uses the defaults, so it remains a
single self-contained file.

## What it does

- **Two status indicators** —
  - the **lifecycle manager** chip (secondary) shows _online_ the moment the control
    plane answers, _offline_ if it can't be reached;
  - the **assistant server** pill (primary) reflects its lifecycle state from
    `/services/local-assistant-server/status`: _Server off_ → _Starting…_ →
    _Warming up…_ (container up but `/health` not yet passing) → _Ready_ (unlocks talk).
    Polled every 3s so idle-shutdown and warm-up are reflected live.
- **Start / Stop** — buttons call the lifecycle manager start/stop endpoints. Voice input
  is disabled until the server is _Ready_.
- **Push-to-talk** — hold the mic button (or the **space bar**) to record; release to send.
  Records mic audio, encodes a 16-bit PCM WAV in-browser, and POSTs it as one chunk to
  `/speak` with `Accept: application/x-ndjson`. **Esc** stops the server (parity with the
  old client's Esc-to-shutdown).
- **Activity feedback** — after you release, the mic button turns into a spinning
  _Thinking…_ indicator ("✔ Message sent · thinking…") and then _Speaking…_ while audio
  plays, so it's always clear the turn was sent and a response is being gathered.
- **Wake chime** — a short synthesized cue plays when the server finishes warming up and
  becomes _Ready_ (only if audio was unlocked by clicking **Start server** first; browser
  autoplay rules block sound before any user gesture). No audio asset required.
- **Lockstep text + audio** — demuxes the NDJSON stream: `text` frames fill the transcript
  in real time while their paired `audio` frames (raw PCM) play back gaplessly via the Web
  Audio API. The user's transcribed text and any tool calls arrive in the response headers
  (`X-Transcript`, `X-Tool-Calls`) and render before the body streams.
- **Waveform** — a canvas driven by an `AnalyserNode` fluctuates in sync with playback.
- **Error handling** — surfaces server errors, mic-permission denial, and network failures;
  refuses to send when no audio was captured; and interrupts any in-progress playback the
  moment a new recording starts.

## Server requirement (CORS)

Because the page is a different origin from the two APIs, both FastAPI apps must send CORS
headers. A minimal `CORSMiddleware` (allowing all origins and exposing the `X-*` response
headers) was added to:

- `local-assistant-server/src/assistant_server/main.py`
- `server-lifecycle-manager/src/server_manager/main.py`

No other server behavior changed.
