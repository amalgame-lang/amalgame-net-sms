# Changelog

## v0.1.0 — 2026-11-19

- `SmsGateway` : SMS Gateway for Android (local server), Twilio, and any
  HTTP gateway by template ; Basic auth ; `Send` (gateway acceptance,
  message id) and `Build` (the request, unsent).
- `SmsText` : GSM 03.38 alphabet, units and segments (GSM 7-bit / UCS-2),
  transliteration to GSM 7-bit, `Fit` to N SMS.
- `Phone.E164` : typed numbers to E.164.
- `SmsEscape` : JSON string, percent-encoding, base64.
- Tests : 38 checks, `Send` against a stand-in gateway.
