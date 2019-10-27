#!/usr/bin/python3

import http.server
import socketserver

with socketserver.TCPServer(("",80),http.server.SimpleHTTPRequestHandler) as httpd:
    print("running")
    httpd.serve_forever()
