# FreePBX for Frappe CRM

Native FreePBX / Asterisk calling inside Frappe CRM. Agents call and answer from the
browser (WebRTC over WSS) using the CRM's own call popup: caller details, timer, mute,
notes, hang up. Calls are written to **CRM Call Log**.

This app owns everything that can live outside the CRM codebase:

| Piece | Where |
|---|---|
| PBX connection and dialing rules | **FreePBX Settings** (Desk) |
| Per-agent extension and password | Extra fields on **CRM Telephony Agent** (added on install) |
| "FreePBX" as a calling medium and call-log medium | Property setters (added on install and on every migrate) |
| `freepbx` flag in the CRM's integration status | `override_whitelisted_methods` |
| SIP credentials API and call-log API | `freepbx.api` |

The browser phone itself (SIP.js + popup) is a small patch to the CRM frontend,
because the CRM's call UI is compiled into its Vue app (`crm-freepbx.patch`).

## Install (development bench, Frappe v15)

```bash
cd ~/frappe-bench

# 1. CRM from your fork (the branch carrying crm-freepbx.patch)
bench get-app https://github.com/<you>/crm --branch freepbx
bench --site <site> install-app crm

# 2. This app
bench --site <site> install-app freepbx     # after copying/cloning it into apps/
bench --site <site> migrate
bench build --app crm
```

If the CRM build fails with `Could not load ../../frappe/ui/src`, update Frappe v15
(`cd apps/frappe && git pull`), then rebuild.

## Configure

1. **FreePBX Settings**: tick *Enabled*, PBX Domain `pbx.landscapers.evergro.co.za`
   (WebSocket URL fills itself as `wss://<domain>:8089/ws`). Adjust the dialing rules
   if you are not in South Africa (`+27...` is dialed as `0...`).
2. **CRM -> Settings -> Telephony** (or Desk -> CRM Telephony Agent): set the agent's
   *FreePBX Extension* and *FreePBX Extension Password*, and pick FreePBX as default medium.
3. Reload CRM. The agent registers on load; the browser asks for microphone permission
   on the first call.

## PBX requirements (already done for 305)

- PJSIP extension with WebRTC options: AVPF, ICE, RTCP mux, media encryption DTLS-SRTP,
  DTLS using the Let's Encrypt certificate.
- Asterisk HTTPS server on TCP 8089 with a certificate valid for the PBX domain.
- UDP 10000-20000 open (RTP), `ice_host_candidates` mapping private to public IP.
- Outbound route and trunk for real numbers. Extension-to-extension calls need neither.

## Testing checklist

1. Console shows `Ready to make and receive calls!`; `pjsip show contacts` lists the extension on `wss`.
2. Call another extension (for example 302): popup shows Calling, Ringing, then timer.
3. Mute, add note, hang up. A **CRM Call Log** appears with medium FreePBX and the note.
4. Call the agent's extension from another phone: popup shows Accept / Reject.
5. Decline and miss calls: statuses Canceled and No Answer.

## Troubleshooting

- **Microphone prompt never appears / `getUserMedia` undefined**: browsers only allow the
  mic on HTTPS or `localhost`. On the dev site `http://localhost:8000`, either browse
  via `http://localhost:8000`, or in Chrome open `chrome://flags/#unsafely-treat-insecure-origin-as-secure`,
  add `http://localhost:8000` (and `:8080` for `yarn dev`), enable it and relaunch.
- **No FreePBX option in CRM**: *FreePBX Settings -> Enabled* is off, or `bench migrate` has not run.
- **Registration fails**: check the browser console, then `asterisk -rvvv` and
  `pjsip set logger on`. Wrong password shows as 401/403.
- **Audio one-way or silent**: UDP range, `ice_host_candidates`, External Address (see PBX notes).
- One browser tab per agent is recommended; a second tab registers the same extension twice.
