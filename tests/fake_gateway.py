#!/usr/bin/env python3
# A stand-in for SMS Gateway for Android's local server, for the tests :
#   POST /message, Basic auth sms:secret, JSON {"textMessage":{"text"},"phoneNumbers":[...]}
#   -> 202 {"id":"m-42","state":"Pending"} (then m-43...) ; 401 on bad credentials ; 400 on a bad body.
#   GET /message/<id> -> its state, like the phone reports it : "Delivered" ;
#   "Failed" with the recipient's error when the text contains FAIL ; "Pending"
#   forever when it contains STUCK (the phone never sends it) ; 404 for an unknown id.
# Every accepted request is appended to <out> (one JSON line), except the
# texts starting with [st] (the status tests).
import base64, json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

port, out = int(sys.argv[1]), sys.argv[2]
msgs = {}

class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def reply(self, code, body):
        b = json.dumps(body).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def authorized(self):
        return self.headers.get('Authorization') == 'Basic ' + base64.b64encode(b'sms:secret').decode()

    def do_GET(self):
        if not self.authorized():
            return self.reply(401, {'message': 'unauthorized'})
        mid = self.path[len('/message/'):] if self.path.startswith('/message/') else ''
        if mid not in msgs:
            return self.reply(404, {'message': 'not found'})
        text, to = msgs[mid]
        rcpt = {'phoneNumber': to[0], 'state': 'Delivered'}
        if 'FAIL' in text:
            rcpt = {'phoneNumber': to[0], 'state': 'Failed', 'error': 'sendSMS: uid 10023 does not have android.permission.SEND_SMS.'}
        elif 'STUCK' in text:
            rcpt = {'phoneNumber': to[0], 'state': 'Pending'}
        self.reply(200, {'id': mid, 'state': rcpt['state'], 'recipients': [rcpt]})

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(n)
        if self.path != '/message':
            return self.reply(404, {'message': 'not found'})
        if not self.authorized():
            return self.reply(401, {'message': 'unauthorized'})
        try:
            m = json.loads(raw)
            text, to = m['textMessage']['text'], m['phoneNumbers']
        except Exception:
            return self.reply(400, {'message': 'bad body'})
        mid = 'm-%d' % (42 + len(msgs))
        msgs[mid] = (text, to)
        if not text.startswith('[st]'):
            with open(out, 'a', encoding='utf-8') as f:
                f.write(json.dumps({'text': text, 'to': to}, ensure_ascii=False) + '\n')
        self.reply(202, {'id': mid, 'state': 'Pending'})

HTTPServer(('127.0.0.1', port), H).serve_forever()
