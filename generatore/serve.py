#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""serve.py - avvia un server locale e stampa l'indirizzo di rete.

Serve per aprire la proposta dal telefono vero collegato allo stesso wifi.
Il cliente finale la aprira' dal telefono: questo e' il modo piu' fedele di provarla.

Uso:
    python generatore/serve.py
    python generatore/serve.py --dir prova-output
    python generatore/serve.py --port 8000
"""

import argparse
import http.server
import os
import socket
import socketserver

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ip_locale():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def main():
    ap = argparse.ArgumentParser(description="Server locale con indirizzo di rete per test da telefono.")
    ap.add_argument("--dir", default=ROOT, help="cartella da servire (default: root del progetto)")
    ap.add_argument("--port", type=int, default=8000, help="porta (default: 8000)")
    args = ap.parse_args()

    directory = os.path.abspath(args.dir)
    if not os.path.isdir(directory):
        raise SystemExit("Cartella non trovata: " + directory)

    os.chdir(directory)
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", args.port), handler) as httpd:
        ip = ip_locale()
        print("Server avviato.")
        print("Cartella:   " + directory)
        print("Locale:     http://127.0.0.1:%d/" % args.port)
        print("Sul telefono (stesso wifi):  http://%s:%d/" % (ip, args.port))
        print("\nEsempi:")
        print("  http://%s:%d/demo-edilcasa/" % (ip, args.port))
        print("  http://%s:%d/demo-serramenti/" % (ip, args.port))
        print("\nPremi Ctrl+C per fermare.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer fermato.")


if __name__ == "__main__":
    main()
