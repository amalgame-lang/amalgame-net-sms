#!/usr/bin/env python3
# A stand-in for SMS Gateway for Android's local server, for the tests :
#   POST /message, Basic auth sms:secret, JSON {"textMessage":{"text"},"phoneNumbers":[...]}
#   -> 202 {"id":"m-42","state":"Pending"} ; 401 on bad credentials ; 400 on a bad body.
# Every accepted request is appended to <out> (one JSON line).
import base64, json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

port, out = int(sys.argv[1]), sys.argv[2]

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

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(n)
        if self.path != '/message':
            return self.reply(404, {'message': 'not found'})
        if self.headers.get('Authorization') != 'Basic ' + base64.b64encode(b'sms:secret').decode():
            return self.reply(401, {'message': 'unauthorized'})
        try:
            m = json.loads(raw)
            text, to = m['textMessage']['text'], m['phoneNumbers']
        except Exception:
            return self.reply(400, {'message': 'bad body'})
        with open(out, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'text': text, 'to': to}, ensure_ascii=False) + '\n')
        self.reply(202, {'id': 'm-42', 'state': 'Pending'})

HTTPServer(('127.0.0.1', port), H).serve_forever()
