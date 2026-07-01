import socket
import threading
import sys
import time
import os
import json
import ipaddress
import subprocess
import shutil

try:
    _args = _pydos_run_args_
except NameError:
    _args = ""

CHAT_PORT     = 7331
DISCOVER_PORT = 7332
APP_TAG       = "PYDOS-LANTERN"
DEFAULT_LOBBY = None


# ── address helpers ───────────────────────────────────────────────────────────

def find_yggdrasil_address():
    if shutil.which('yggdrasilctl'):
        try:
            result = subprocess.run(
                ['sudo', 'yggdrasilctl', 'getself'],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if 'IPv6 address' in line:
                    for p in line.split('│'):
                        p = p.strip()
                        if p and ':' in p and not p.startswith('IPv6'):
                            return p
        except (subprocess.TimeoutExpired, OSError):
            pass
    try:
        with open('/proc/net/if_inet6') as f:
            for line in f:
                fields = line.split()
                if not fields or len(fields[0]) != 32:
                    continue
                raw = bytes.fromhex(fields[0])
                if (raw[0] & 0xFE) == 0x02:
                    addr = str(ipaddress.IPv6Address(raw))
                    if not addr.startswith('fe'):
                        return addr
    except (FileNotFoundError, PermissionError, ValueError):
        pass
    return None

def get_lan_addresses():
    addrs = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        addrs.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            ip = info[4][0]
            if ':' not in ip and not ip.startswith('127.'):
                addrs.add(ip)
    except OSError:
        pass
    return sorted(addrs)

def _now():
    return time.strftime('%H:%M:%S')


# ── server ────────────────────────────────────────────────────────────────────

class LanternServer:
    def __init__(self, room, port):
        self.room    = room
        self.port    = port
        self.clients = {}
        self.lock    = threading.Lock()
        self.running = True
        self._srv    = None

    def broadcast(self, text, exclude=None):
        dead = []
        with self.lock:
            for conn in self.clients:
                if conn is exclude:
                    continue
                try:
                    conn.sendall((text + "\n").encode())
                except OSError:
                    dead.append(conn)
        for conn in dead:
            self._drop(conn)

    def _drop(self, conn):
        with self.lock:
            nick = self.clients.pop(conn, None)
        try:
            conn.close()
        except OSError:
            pass
        if nick:
            self.broadcast(f"* {nick} left  [{_now()}]")
            print(f"\n[Lantern] {nick} disconnected")

    def handle_client(self, conn, addr):
        try:
            f     = conn.makefile('r', encoding='utf-8', newline='\n')
            first = f.readline().strip()
            if not first.startswith("HELLO "):
                conn.close(); return
            nick = first[6:].strip()[:24] or f"guest{addr[1] % 1000}"
            with self.lock:
                taken = set(self.clients.values())
            while nick in taken:
                nick = nick + "_"
            with self.lock:
                self.clients[conn] = nick
            conn.sendall(f"WELCOME {self.room} {len(self.clients)}\n".encode())
            print(f"\n[Lantern] {nick} connected from {addr[0]}")
            self.broadcast(f"* {nick} joined  [{_now()}]", exclude=conn)
            for line in f:
                line = line.rstrip("\n")
                if not line:
                    continue
                if line == "/quit":
                    break
                elif line.startswith("/nick "):
                    new = line[6:].strip()[:24]
                    if new:
                        with self.lock:
                            self.clients[conn] = new
                        self.broadcast(f"* {nick} is now known as {new}")
                        nick = new
                elif line == "/who":
                    with self.lock:
                        names = ", ".join(self.clients.values())
                    conn.sendall(f"* online: {names}\n".encode())
                else:
                    self.broadcast(f"[{_now()}] {nick}: {line}", exclude=conn)
        except (OSError, UnicodeDecodeError):
            pass
        finally:
            self._drop(conn)

    def announce_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        payload = json.dumps({
            "app": APP_TAG, "room": self.room, "port": self.port
        }).encode()
        while self.running:
            try:
                sock.sendto(payload, ('<broadcast>', DISCOVER_PORT))
            except OSError:
                pass
            time.sleep(2)
        sock.close()

    def _accept_loop(self):
        while self.running:
            try:
                conn, addr = self._srv.accept()
                threading.Thread(
                    target=self.handle_client,
                    args=(conn, addr), daemon=True
                ).start()
            except OSError:
                break

    def serve_background(self):
        """Start server in background thread. Returns immediately."""
        self._srv = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._srv.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except (AttributeError, OSError):
            pass
        self._srv.bind(('::', self.port))
        self._srv.listen(16)

        print(f"\n=== LANTERN :: hosting '{self.room}' on port {self.port} ===")
        ygg = find_yggdrasil_address()
        if ygg:
            print(f"Yggdrasil : [{ygg}]  →  run community join {ygg}")
        else:
            print("Yggdrasil : not detected")
        for ip in get_lan_addresses():
            print(f"LAN       : {ip}  →  run community join {ip}")
        print()

        threading.Thread(target=self.announce_loop, daemon=True).start()
        threading.Thread(target=self._accept_loop,  daemon=True).start()

    def serve_blocking(self):
        """Blocking serve — used for host-only mode (no client)."""
        self.serve_background()
        print("Press Ctrl+C to stop hosting.\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[Lantern] Shutting down lobby...")
        finally:
            self.shutdown()

    def shutdown(self):
        self.running = False
        try:
            self._srv.close()
        except Exception:
            pass


# ── LAN discovery ─────────────────────────────────────────────────────────────

def discover_lan_lobbies(timeout=3):
    found = {}
    sock  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(('', DISCOVER_PORT))
    except OSError:
        return found
    sock.settimeout(0.5)
    end = time.time() + timeout
    while time.time() < end:
        try:
            data, addr = sock.recvfrom(2048)
            payload    = json.loads(data.decode())
            if payload.get("app") == APP_TAG:
                found[addr[0]] = payload
        except (socket.timeout, ValueError, OSError):
            continue
    sock.close()
    return found

def discover_background(results, done_event):
    """Run LAN scan in background, store results, set event when done."""
    found = discover_lan_lobbies(timeout=3)
    results.update(found)
    done_event.set()


# ── client ────────────────────────────────────────────────────────────────────

def join_lobby(address, port, nick):
    family = socket.AF_INET6 if ':' in address else socket.AF_INET
    sock   = socket.socket(family, socket.SOCK_STREAM)
    sock.settimeout(10)
    try:
        sock.connect((address, port))
    except OSError as e:
        print(f"[Lantern] Could not connect: {e}")
        return
    sock.settimeout(None)
    sock.sendall(f"HELLO {nick}\n".encode())

    stop   = threading.Event()
    PROMPT = f"{nick}> "

    def listen():
        f = sock.makefile('r', encoding='utf-8', newline='\n')
        try:
            for line in f:
                line = line.rstrip("\n")
                if not line:
                    continue
                if line.startswith("WELCOME "):
                    parts = line.split()
                    room  = parts[1] if len(parts) > 1 else "?"
                    users = parts[2] if len(parts) > 2 else "?"
                    print(f"\r[Lantern] Joined '{room}' — {users} user(s) online.")
                    print(PROMPT, end="", flush=True)
                    continue
                # clear input line, print message, reprint prompt
                sys.stdout.write(
                    f"\r{' ' * (len(PROMPT) + 80)}\r{line}\n{PROMPT}"
                )
                sys.stdout.flush()
        except OSError:
            pass
        finally:
            stop.set()
            sys.stdout.write("\r[Lantern] Connection closed.\n")
            sys.stdout.flush()

    threading.Thread(target=listen, daemon=True).start()
    print("[Lantern] Connected.  /who  /nick <name>  /quit\n")

    try:
        while not stop.is_set():
            sys.stdout.write(PROMPT)
            sys.stdout.flush()
            line = sys.stdin.readline()
            if not line or stop.is_set():
                break
            line = line.rstrip("\n")
            if stop.is_set():
                break
            try:
                sock.sendall((line + "\n").encode())
            except OSError:
                break
            if line.strip() == "/quit":
                break
            if line.startswith("/nick "):
                new = line[6:].strip()[:24]
                if new:
                    PROMPT = f"{new}> "
    except KeyboardInterrupt:
        try:
            sock.sendall(b"/quit\n")
        except OSError:
            pass
    finally:
        sock.close()


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    raw   = _args.strip() if isinstance(_args, str) else ""
    parts = raw.split(None, 1)
    sub   = parts[0].lower() if parts else ""
    rest  = parts[1].strip() if len(parts) > 1 else ""

    # ── run community host [room] ─────────────────────────────────────────
    if sub == "host":
        room = rest or "Lantern"
        LanternServer(room, CHAT_PORT).serve_blocking()
        return

    # ── run community join <addr> [port] ──────────────────────────────────
    if sub == "join":
        if not rest:
            print("Usage: run community join <address> [port]")
            return
        bits    = rest.split()
        address = bits[0].strip('[]')
        port    = int(bits[1]) if len(bits) > 1 else CHAT_PORT
        nick    = input("Nickname: ").strip() or os.environ.get('USER', 'guest')
        join_lobby(address, port, nick)
        return

    # ── run community (interactive) ───────────────────────────────────────
    print("=== LANTERN ===")
    print("Scanning for lobbies on your network...", end="", flush=True)

    results    = {}
    done_event = threading.Event()
    threading.Thread(
        target=discover_background,
        args=(results, done_event),
        daemon=True
    ).start()

    # let scan run in background — wait up to 3s but don't block prompt
    done_event.wait(timeout=3)
    print(" done.")

    if results:
        options = list(results.items())
        print()
        for i, (ip, info) in enumerate(options, 1):
            print(f"  {i}) {info.get('room','?')}  ({ip}:{info.get('port', CHAT_PORT)})")
        print()
        choice = input(
            f"Pick [1-{len(options)}], enter an address, or 'host' to start your own: "
        ).strip()

        if choice.isdigit() and 1 <= int(choice) <= len(options):
            ip, info = options[int(choice) - 1]
            nick = input("Nickname: ").strip() or os.environ.get('USER', 'guest')
            join_lobby(ip, info.get('port', CHAT_PORT), nick)
            return

        if choice.lower() == 'host':
            room   = input("Room name: ").strip() or "Lantern"
            server = LanternServer(room, CHAT_PORT)
            server.serve_background()
            nick = input("Nickname: ").strip() or os.environ.get('USER', 'guest')
            time.sleep(0.5)  # let server socket bind before we connect
            join_lobby('127.0.0.1', CHAT_PORT, nick)
            return

        if choice:
            nick = input("Nickname: ").strip() or os.environ.get('USER', 'guest')
            join_lobby(choice.strip('[]'), CHAT_PORT, nick)
            return

    # no lobbies found
    print("No lobby found on LAN.\n")
    choice = input(
        "Enter an address to join, 'host' to start your own, or Enter to abort: "
    ).strip()

    if not choice:
        if DEFAULT_LOBBY:
            nick = input("Nickname: ").strip() or os.environ.get('USER', 'guest')
            join_lobby(DEFAULT_LOBBY, CHAT_PORT, nick)
        else:
            print("Aborted.")
        return

    if choice.lower() == 'host':
        room   = input("Room name: ").strip() or "Lantern"
        server = LanternServer(room, CHAT_PORT)
        server.serve_background()
        nick = input("Nickname: ").strip() or os.environ.get('USER', 'guest')
        time.sleep(0.5)
        join_lobby('127.0.0.1', CHAT_PORT, nick)
        return

    nick = input("Nickname: ").strip() or os.environ.get('USER', 'guest')
    join_lobby(choice.strip('[]'), CHAT_PORT, nick)


main()
