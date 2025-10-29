"""Run the landing page and optionally launch dashboards.

Usage examples (PowerShell):
  # Serve only the landing page on port 8000
  python .\landing\run_landing.py

  # Serve landing and start the Dash app using default command (python Main.py)
  python .\landing\run_landing.py --start-dash

  # Use a custom command to start dashboards
  python .\landing\run_landing.py --start-dash --dash-cmd "python Main.py --port 8050"

The script will:
- Serve the `landing/` folder over HTTP (default port 8000) so you can open the slideshow.
- Optionally spawn a child process for your Dash app. Child processes are terminated when you stop this script.

Notes:
- This does not edit your dashboards. It only runs them as separate processes if you ask it to.
- If your Dash app is already running, don't use --start-dash; just run this script to serve the landing page.
"""

import argparse
import os
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import urllib.request
import urllib.error



ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LANDING_DIR = os.path.join(ROOT, 'landing')

# Globals used by the HTTP handler to control the Dash subprocess
DASH_PROCESS = None
START_COMMAND = None
DASH_PORT = 8051

# New global for ngrok process(es)
NGROK_PROCESS = None


def serve_landing(port: int):
    """Serve the landing directory on the given port."""
    # Serve from the repository root so sibling folders like `assets/` are reachable
    os.chdir(ROOT)

    class Handler(SimpleHTTPRequestHandler):
        def do_POST(self):
            global DASH_PROCESS, START_COMMAND
            if self.path == '/start_dash':
                # Start the Dash subprocess if it's not already running
                # If process already exists, just report status (and check responsiveness)
                if DASH_PROCESS is not None:
                    ready = False
                    try:
                        urllib.request.urlopen(f'http://localhost:{DASH_PORT}/', timeout=0.8)
                        ready = True
                    except Exception:
                        ready = False
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    resp = json.dumps({"started": False, "ready": ready}).encode('utf-8')
                    self.wfile.write(resp)
                    return

                if not START_COMMAND:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"started": false, "reason": "no_command"}')
                    return

                try:
                    DASH_PROCESS = start_subprocess(START_COMMAND, cwd=ROOT)
                    # After starting, poll the dash port until it's responsive or timeout
                    waited = 0.0
                    timeout = 15.0
                    interval = 0.5
                    ready = False
                    while waited < timeout:
                        try:
                            urllib.request.urlopen(f'http://localhost:{DASH_PORT}/', timeout=0.8)
                            ready = True
                            break
                        except Exception:
                            time.sleep(interval)
                            waited += interval

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    resp = json.dumps({"started": True, "ready": ready, "waited": waited}).encode('utf-8')
                    self.wfile.write(resp)
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    payload = json.dumps({"started": False, "error": str(e)}).encode('utf-8')
                    self.wfile.write(payload)
                return
            return super().do_POST()

    handler = Handler
    server = ThreadingHTTPServer(('', port), handler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def start_subprocess(cmd: str, cwd: str = None):
    """Start a subprocess and return the Popen object."""
    if cwd is None:
        cwd = ROOT
    # On Windows, use shell=True if cmd is a string command that needs shell features
    # We'll try to split when possible and fallback to shell
    try:
        # If cmd looks like a list in string form, keep it as string for shell
        proc = subprocess.Popen(cmd, cwd=cwd, shell=True)
        print(f"Started subprocess (pid={proc.pid}) with command: {cmd}")
        # Give the process a short moment; if it exited quickly, report the exit code
        time.sleep(0.6)
        if proc.poll() is not None:
            print(f"Subprocess exited quickly with return code {proc.returncode}")
    except Exception as e:
        print('Failed to start subprocess:', e)
        proc = None
    return proc


def start_ngrok(port: int, region: str = None):
    """
    Start an ngrok HTTP tunnel for the given port and return the public URL.
    Requires 'ngrok' binary available on PATH.
    Returns (proc, public_url) or (None, None) on failure.
    """
    import time
    global NGROK_PROCESS
    try:
        cmd = ["ngrok", "http", str(port)]
        if region:
            cmd += ["--region", region]
        NGROK_PROCESS = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print("Failed to start ngrok:", e)
        return None, None

    # Wait for ngrok API to appear and return tunnel info
    api_url = "http://127.0.0.1:4040/api/tunnels"
    timeout = 15.0
    waited = 0.0
    interval = 0.5
    public_url = None
    while waited < timeout:
        try:
            with urllib.request.urlopen(api_url, timeout=1.0) as resp:
                data = json.load(resp)
                tunnels = data.get("tunnels", [])
                if tunnels:
                    # Prefer https tunnel if available
                    for t in tunnels:
                        if t.get("proto") == "https":
                            public_url = t.get("public_url")
                            break
                    if not public_url:
                        public_url = tunnels[0].get("public_url")
                    break
        except Exception:
            time.sleep(interval)
            waited += interval
    if public_url:
        return NGROK_PROCESS, public_url
    # if no URL found, try to cleanup and return None
    try:
        if NGROK_PROCESS:
            NGROK_PROCESS.terminate()
            NGROK_PROCESS = None
    except Exception:
        pass
    return None, None


def main():
    parser = argparse.ArgumentParser(description='Serve landing page and optionally start Dash apps')
    parser.add_argument('--port', type=int, default=8000, help='Port to serve landing page on')
    parser.add_argument('--start-dash', action='store_true', help='Also start the Dash app using --dash-cmd')
    import sys as _sys
    default_cmd = f'"{_sys.executable}" Main.py'
    parser.add_argument('--dash-cmd', type=str, default=default_cmd, help='Command to start the Dash app (string form)')
    parser.add_argument('--dash-port', type=int, default=8051, help='Port where the Dash app listens')
    parser.add_argument('--no-open', action='store_true', help='Do not open the web browser automatically')

    # New flag to create a public ngrok tunnel for the landing page (and Dash when starting it)
    parser.add_argument('--public', action='store_true', help='Expose landing page (and Dash) via ngrok and print public URL(s)')

    args = parser.parse_args()

    if not os.path.isdir(LANDING_DIR):
        print('Error: landing folder not found at', LANDING_DIR)
        sys.exit(1)

    print('Serving landing page from:', LANDING_DIR)
    server, thread = serve_landing(args.port)

    # Expose the configured start command to the handler
    global START_COMMAND, DASH_PROCESS, DASH_PORT
    START_COMMAND = args.dash_cmd
    DASH_PORT = args.dash_port

    DASH_PROCESS = None
    if args.start_dash:
        print('Starting Dash app with command:', args.dash_cmd)
        DASH_PROCESS = start_subprocess(args.dash_cmd, cwd=ROOT)
        time.sleep(0.5)

    # If requested, start ngrok for landing (and for Dash if started)
    global NGROK_PROCESS
    landing_public = None
    dash_public = None
    if args.public:
        proc, landing_public = start_ngrok(args.port)
        if proc and landing_public:
            print('Landing page public URL (ngrok):', landing_public)
            if not args.no_open:
                try:
                    webbrowser.open(landing_public)
                except Exception:
                    pass
        else:
            print('ngrok failed to start or did not return a public URL. Make sure ngrok is installed and on PATH.')

        # Start a separate ngrok tunnel for the Dash app if we also launched it
        if args.start_dash:
            proc2, dash_public = start_ngrok(args.dash_port)
            if proc2 and dash_public:
                print('Dash app public URL (ngrok):', dash_public)
            else:
                print('ngrok failed to create a tunnel for Dash (is ngrok installed?).')

    # Open the landing page specifically (served from the workspace root) if not using ngrok public open
    url = f'http://localhost:{args.port}/landing/index.html'
    print('Landing page URL:', url)
    if not args.no_open and not (args.public and landing_public):
        try:
            webbrowser.open(url)
        except Exception:
            pass

    def _shutdown(signum=None, frame=None):
        print('\nShutting down...')
        try:
            server.shutdown()
        except Exception:
            pass
        try:
            server.server_close()
        except Exception:
            pass
        if DASH_PROCESS:
            try:
                DASH_PROCESS.terminate()
                DASH_PROCESS.wait(timeout=3)
            except Exception:
                try:
                    DASH_PROCESS.kill()
                except Exception:
                    pass
        # terminate ngrok if started
        global NGROK_PROCESS
        try:
            if NGROK_PROCESS:
                NGROK_PROCESS.terminate()
                NGROK_PROCESS = None
        except Exception:
            pass
        sys.exit(0)

    # Handle Ctrl+C
    try:
        signal.signal(signal.SIGINT, _shutdown)
    except Exception:
        # Windows might raise if run in certain contexts; KeyboardInterrupt will also work
        pass

    print('Press Ctrl+C to stop.')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        _shutdown()


if __name__ == '__main__':
    main()
