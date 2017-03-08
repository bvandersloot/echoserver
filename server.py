#!/usr/bin/python3
import http.server
import threading
import time

state = {}
mutex = threading.Lock()
MESSAGE_LEN_MAX = 20*1024*1024
MESSAGE_N_MAX = 5
TIMEOUT = 30

class SendSeqHandler(http.server.BaseHTTPRequestHandler):
    global state
    #path -> (data, time), max 5 entries (timeout after 30s), 20M max in data
    def do_GET(self):
        mutex.acquire()
        if self.path not in state:
            mutex.release()
            self.send_full_response(404, str.encode(""))
            return
        b = state[self.path][0]
        mutex.release()
        self.send_full_response(200, b)
        return
    def do_POST(self):
        mutex.acquire()
        close_connection = True
        b = self.rfile.read(int(self.headers['Content-Length']))
        if len(b) > MESSAGE_LEN_MAX:
            mutex.release()
            self.send_full_response(400, str.encode(""))
            return
        if self.path not in state and len(state) > MESSAGE_N_MAX - 1:
            worked = False
            for k in state:
                if time.time() - state[k][1] > TIMEOUT:
                    del state[k]
                    worked = True
            if not worked:
                mutex.release()
                self.send_full_response(500, str.encode(""))
                return
        state[self.path] = (b, time.time())
        mutex.release()
        self.send_full_response(200, b)
        return
    def send_full_response(self, code, body):
        self.send_response(code)
        self.send_header("ContentType", "text/html")
        self.end_headers()
        if len(body) > 0:
            self.wfile.write(body)

def run(server_class=http.server.HTTPServer, handler_class=SendSeqHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

run()
