#!/usr/bin/env python3
"""Render the social share image, rmxy-1/assets/shots/og.png (1200 x 630 at 2x), from tools/og.html:
the XY-1 wordmark, the headline, and the app on a drawn iPad.

The screen is composed losslessly from tools/og-source/ipad-fold-dark.png: the owner's lossless window
screenshot of the Debug standalone (Dark theme, Fold editor open, pad held), 1180 pt wide at 2x, converted
from its embedded Adobe RGB profile to sRGB, cropped to the window content, with the mouse pointer patched
from the pad one dot-spacing (84 px) to its left. Its macOS-only test row (top 150 px, see
docs/capture-notes.md) is replaced by the iPad status-bar area in the app's own background, so the app sits
exactly where it would on the 1180 x 820 pt iPad screen. The page draws the status bar and the device.

Needs Google Chrome and websocket-client. Usage: python3 tools/build_og.py
"""
import base64
import functools
import http.server
import json
import pathlib
import subprocess
import tempfile
import threading
import time
import urllib.request

import websocket
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'rmxy-1' / 'assets' / 'shots' / 'og.png'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
PORT = 9334
SCREEN = ROOT / 'tools' / 'og-screen.png'
VOID = (13, 18, 22)  # the app's background, #0D1216


def compose_screen():
    cap = Image.open(ROOT / 'tools' / 'og-source' / 'ipad-fold-dark.png').convert('RGB')
    body = cap.crop((0, 150, cap.width, cap.height))          # below the macOS test row
    screen = Image.new('RGB', (2360, 1640), VOID)
    top = 54                                                   # the rail lands 31 pt down: status bar + app margin
    screen.paste(body.crop((0, 0, body.width, screen.height - top)), (0, top))
    screen.paste(VOID, (0, top, screen.width, top + 8))        # the row's shadow, back to background
    screen.save(SCREEN)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


handler = functools.partial(Quiet, directory=str(ROOT))
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}/tools/og.html'

compose_screen()
with tempfile.TemporaryDirectory() as profile:
    chrome = subprocess.Popen([CHROME, '--headless=new', f'--remote-debugging-port={PORT}', f'--remote-allow-origins=http://127.0.0.1:{PORT}',
                               f'--user-data-dir={profile}', '--hide-scrollbars', '--window-size=1200,630', 'about:blank'],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                page = next(t for t in json.load(urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json')) if t['type'] == 'page')
                break
            except Exception:
                time.sleep(0.2)
        ws = websocket.create_connection(page['webSocketDebuggerUrl'], timeout=30)
        seq = 0

        def cmd(method, **params):
            global seq
            seq += 1
            ws.send(json.dumps({'id': seq, 'method': method, 'params': params}))
            while True:
                msg = json.loads(ws.recv())
                if msg.get('id') == seq:
                    return msg.get('result', {})

        cmd('Emulation.setDeviceMetricsOverride', width=1200, height=630, deviceScaleFactor=2, mobile=False)
        cmd('Emulation.setEmulatedMedia', features=[{'name': 'prefers-reduced-motion', 'value': 'reduce'}])
        cmd('Page.enable')
        cmd('Page.navigate', url=url)
        time.sleep(3)
        png = cmd('Page.captureScreenshot', format='png', clip={'x': 0, 'y': 0, 'width': 1200, 'height': 630, 'scale': 1}, captureBeyondViewport=False)['data']
        OUT.write_bytes(base64.b64decode(png))
        print(f'wrote {OUT.relative_to(ROOT)}')
    finally:
        chrome.kill()
        server.shutdown()
        SCREEN.unlink(missing_ok=True)
