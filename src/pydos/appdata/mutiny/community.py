import socket
import threading
import sys
import time
import os
import json
import ipaddress

try:
    _args = _pydos_run_args_
except NameError:
    _args = ""

CHAT_PORT = 7331       # TCP: the actual chat lobby
DISCOVER_PORT = 7332   # UDP: LAN "is anyone hosting?" broadcast
APP_TAG = "PYDOS-MUTINY"
DEFAULT_LOBBY = None    # set to a known stable address (e.g. your own Yggdrasil
                         # address) to give everyone running this a default to join


def find_yggdrasil_address():
    """Scan /proc/net/if_inet6 for an address in Yggdrasil's 200::/7 range.
    Works without yggdrasilctl, so it also works inside Termux if the
    official Yggdrasil Android app is running (shared kernel network stack)."""
    try:
        with open('/proc/net/if_inet6') as f:
            for line in f:
                fields = line.split()
                if not fields:
                    continue
                addr_hex = fields[0]
                if len(addr_hex) == 32 and addr_hex[:2] in ('02', '03'):
                    raw = bytes.fromhex(addr_hex)
                    return str(ipaddress.IPv6Address(raw))
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


# ---------------- SERVER (HOST A LOBBY) ----------------

class MutinyServer:
    def __init__(self, room, port):
        self.room = room
        self.port = port
        self.clients = {}
        self.lock = threading.Lock()
        self.running = True

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
            print(f"[Mutiny] {nick} disconnected")

    def handle_client(self, conn, addr):
        try:
            f = conn.makefile('r', encoding='utf-8', newline='\n')
            first = f.readline().strip()
            if not first.startswith("HELLO "):
                conn.close()
                return
            nick = first[6:].strip()[:24] or f"guest{addr[1] % 1000}"
            with self.lock:
                taken = set(self.clients.values())
            while nick in taken:
                nick = nick + "_"
            with self.lock:
                self.clients[conn] = nick
            conn.sendall(f"WELCOME {self.room} {len(self.clients)}\n".encode())
            print(f"[Mutiny] {nick} connected from {addr[0]}")
            self.broadcast(f"* {nick} joined  [{_now()}]", exclude=conn)
            for line in f:
                line = line.rstrip("\n")
                if not line:
                    continue
                if line == "/quit":
                    break
                elif line.startswith("/nick "):
                    newnick = line[6:].strip()[:24]
                    if newnick:
                        with self.lock:
                            self.clients[conn] = newnick
                        self.broadcast(f"* {nick} is now known as {newnick}")
                        nick = newnick
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
        payload = json.dumps({"app": APP_TAG, "room": self.room, "port": self.port}).encode()
        while self.running:
            try:
                sock.sendto(payload, ('<broadcast>', DISCOVER_PORT))
            except OSError:
                pass
            time.sleep(2)

    def serve(self):
        srv = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            srv.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except (AttributeError, OSError):
            pass
        srv.bind(('::', self.port))
        srv.listen(16)

        print(f"\n=== MUTINY COMMUNITY :: hosting '{self.room}' on port {self.port} ===")
        ygg = find_yggdrasil_address()
        if ygg:
            print(f"Yggdrasil address : [{ygg}]  ->  run community join {ygg}")
        else:
            print("Yggdrasil address : not detected (yggdrasil not running here?)")
        for ip in get_lan_addresses():
            print(f"LAN address       : {ip}  ->  run community join {ip}")
        print("Press Ctrl+C to stop hosting.\n")

        threading.Thread(target=self.announce_loop, daemon=True).start()
        try:
            while True:
                conn, addr = srv.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("\n[Mutiny] Shutting down lobby...")
        finally:
            self.running = False
            srv.close()


# ---------------- CLIENT (JOIN A LOBBY) ----------------

def discover_lan_lobbies(timeout=3):
    found = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
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
            payload = json.loads(data.decode())
            if payload.get("app") == APP_TAG:
                found[addr[0]] = payload
        except (socket.timeout, ValueError, OSError):
            continue
    sock.close()
    return found


def join_lobby(address, port, nick):
    family = socket.AF_INET6 if ':' in address else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_STREAM)
    sock.settimeout(10)
    try:
        sock.connect((address, port))
    except OSError as e:
        print(f"[Mutiny] Could not connect: {e}")
        return
    sock.settimeout(None)
    sock.sendall(f"HELLO {nick}\n".encode())

    stop = threading.Event()
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
                    print(f"\r[Mutiny] Joined '{room}' — {users} user(s) online.")
                    print(PROMPT, end="", flush=True)
                    continue
                # Clear current input line, print message, reprint prompt
                sys.stdout.write(f"\r{' ' * (len(PROMPT) + 80)}\r{line}\n{PROMPT}")
                sys.stdout.flush()
        except OSError:
            pass
        finally:
            stop.set()
            # Unblock input() by sending a newline to stdin (Unix only)
            try:
                import termios, tty
                sys.stdout.write(f"\r[Mutiny] Connection closed.\n")
                sys.stdout.flush()
            except ImportError:
                pass

    threading.Thread(target=listen, daemon=True).start()

    print("[Mutiny] Connected. /who  /nick <name>  /quit\n")
    try:
        while not stop.is_set():
            try:
                sys.stdout.write(PROMPT)
                sys.stdout.flush()
                line = sys.stdin.readline()
                if not line or stop.is_set():
                    break
                line = line.rstrip("\n")
            except EOFError:
                break
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

# ---------------- ENTRY POINT ----------------

def main():
    raw   = _args.strip() if isinstance(_args, str) else ""
    parts = raw.split(None, 1)
    sub   = parts[0].lower() if parts else ""
    rest  = parts[1].strip() if len(parts) > 1 else ""
    

    if sub == "host":
        room = rest or "Mutiny"
        MutinyServer(room, CHAT_PORT).serve()
        return

    if sub == "join":
        if not rest:
            print("Usage: run community join <address> [port]")
            return
        bits = rest.split()
        address = bits[0].strip('[]')
        port = int(bits[1]) if len(bits) > 1 else CHAT_PORT
        nick = input("Nickname: ").strip() or os.environ.get('USER', 'guest')
        join_lobby(address, port, nick)
        return

    print("=== MUTINY COMMUNITY ===")
    print("Looking for lobbies on your network...")
    found = discover_lan_lobbies(timeout=3)
    if found:
        options = list(found.items())
        for i, (ip, info) in enumerate(options, 1):
            print(f"  {i}) {info.get('room')}  ({ip}:{info.get('port')})")
        choice = input(f"Pick a lobby [1-{len(options)}] or press Enter to type an address: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            ip, info = options[int(choice) - 1]
            nick = input("Nickname: ").strip() or os.environ.get('USER', 'guest')
            join_lobby(ip, info.get('port', CHAT_PORT), nick)
            return

    print("No lobby found on LAN.")
    address = input("Host address (LAN IP or Yggdrasil address), or 'host' to start your own: ").strip()
    if address.lower() == 'host':
        room = input("Room name: ").strip() or "Mutiny"
        MutinyServer(room, CHAT_PORT).serve()
        return
    if not address:
        if DEFAULT_LOBBY:
            address = DEFAULT_LOBBY
        else:
            print("No address given, and no default lobby configured. Aborting.")
            return
    nick = input("Nickname: ").strip() or os.environ.get('USER', 'guest')
    join_lobby(address.strip('[]'), CHAT_PORT, nick)


main()
