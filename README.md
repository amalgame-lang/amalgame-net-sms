# amalgame-net-sms

Send SMS through an HTTP gateway, from Amalgame.

```amalgame
import Amalgame.Net.Sms

let gw: SmsGateway = SmsGateway.SmsGate("http://192.168.1.20:8080", "sms", "secret")
let to: string = Phone.E164("06 12 34 56 78", "33")              // "+33612345678"
let r: SmsResult = gw.Send(to, SmsText.Fit("Pompe P2 en défaut, débit 0 m³/h", 1))
if (!r.Ok) { Console.WriteError(r.Error) }                        // r.StatusCode, r.Id
```

## Gateways

| Constructor | Gateway | Request |
|---|---|---|
| `SmsGateway.SmsGate(url, user, password)` | [SMS Gateway for Android](https://github.com/capcom6/android-sms-gateway), local server : an Android phone sends through its own SIM | `POST <url>/message`, Basic auth, `{"textMessage":{"text"},"phoneNumbers":[…]}` |
| `SmsGateway.Twilio(accountSid, authToken, from)` | Twilio Programmable Messaging | `POST /2010-04-01/Accounts/<sid>/Messages.json`, form `To`/`From`/`Body` |
| `SmsGateway.Template(method, url, contentType, body)` | any other HTTP gateway : 4G routers, operators | `{to}`, `{text}`, `{from}` in the URL (percent-encoded) and the body (JSON-escaped when the content type is JSON, percent-encoded otherwise) ; `.WithBasicAuth(user, password)`, `.WithFrom(sender)` |

`Send` reports the gateway's **acceptance** (2xx, with its message id in
`r.Id` when it gives one), not the delivery to the handset : that comes
later from the gateway (SMS Gateway for Android : delivery reports and
webhooks ; Twilio : status callbacks). `StatusCode` is 0 when the
gateway cannot be reached, -1 when the request is refused before
sending (number not in E.164, empty text). `Build(to, text)` returns the
request without sending it.

### A phone over USB

With SMS Gateway for Android on a phone plugged in by USB (USB debugging
on), `adb forward tcp:8080 tcp:8080` makes its local server
`http://127.0.0.1:8080` on the computer : no Wi-Fi network needed.

## Text : one SMS, not three

A single character outside the GSM 03.38 alphabet (`ê`, `ç`, `³`, `«`,
`’`) sends the whole message in UCS-2 : 70 characters per SMS instead of
160, and an alarm is cut in three. `SmsText` deals with it :

| | |
|---|---|
| `SmsText.IsGsm7(text)` | every character is in the GSM 7-bit alphabet (basic or extension table) |
| `SmsText.Units(text)` | length in septets (GSM 7-bit, `€ ^ { } [ ] ~ \| \\` count 2) or UTF-16 units (UCS-2) |
| `SmsText.Segments(text)` | number of SMS : 160 then 153 per part (GSM 7-bit), 70 then 67 (UCS-2) |
| `SmsText.ToGsm7(text)` | transliterated to GSM 7-bit : `ê` → `e`, `m³` → `m3`, `«` → `"`, `–` → `-`, `°` → `deg`, `…` → `...`, no-break spaces → space ; `?` for what has no equivalent. `é è à ù É Ç` are GSM and stay |
| `SmsText.Fit(text, n)` | `ToGsm7`, cut to fit in `n` SMS, `...` at the cut |

## Phone numbers

`Phone.E164(typed, country)` : `"06 12 34 56 78"`, `"06.12.34.56.78"`,
`"+33 6 12 34 56 78"` and `"0033612345678"` all give `"+33612345678"`
with country `"33"`. Spaces, dots, dashes, slashes, brackets and
no-break spaces are dropped ; letters, or a number too short or too long
for E.164, give `""`.

## Tests

```bash
./tests/run_am_tests.sh [amc]
```

38 checks : the alphabet and segment counts, transliteration, E.164,
escaping, the exact request of each gateway, and `Send` against a stand-in
for SMS Gateway for Android (`tests/fake_gateway.py`, python3) : accepted
with its id, 401 on a wrong password, unreachable gateway, number refused
before sending, and the message as received by the gateway.

## Dependencies

`amalgame-net-http` (HttpClient, HTTP and HTTPS), `amalgame-crypto` (byte
helpers). Pure Amalgame, no FFI. Apache-2.0.
