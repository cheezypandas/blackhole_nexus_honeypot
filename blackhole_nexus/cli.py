#!/usr/bin/env python3
import curses
import subprocess
import threading
import queue
import time
import os
from pathlib import Path

# honey-themed colour IDs
HONEY = {
    "title": 1,
    "menu": 2,
    "status_running": 3,
    "status_stopped": 4,
    "box": 5,
    "text": 6,
}

class HoneypotManager:
    def __init__(self):
        self.processes = {}
        self.log_queue = queue.Queue()
        self.running = False
        self.base_dir = Path(__file__).parent

        # Create the logging folder if it doesn't exist
        self.logging_dir = self.base_dir / "logging"
        self.logging_dir.mkdir(parents=True, exist_ok=True)

        # Define LOG_DIR before using it
        LOG_DIR = self.logging_dir  # or: self.base_dir.parent / "logging"

        # Define where each component logs within the logging directory
        self.log_paths = {
            "cowrie": LOG_DIR / "cowrie.log",
            "syscall": LOG_DIR / "syscall_hooks.log",
            "threat_intel": LOG_DIR / "threat_intel.json",
        }


    def start_services(self):
        """Start all services and write to logs immediately."""
        print("\033[93m[🍯] Logs are being compiled in: logging/\033[0m")

        try:
            # Cowrie
            subprocess.run([ 
                "docker-compose", "-f",
                str(self.base_dir/"honeypots/cowrie/docker-compose.yml"),
                "up", "-d"
            ], cwd=self.base_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._log_event("cowrie", f"Started Cowrie container, logging → {self.log_paths['cowrie']}")

            # ELK (for completeness, not shown in boxes)
            subprocess.run([ 
                "docker-compose", "-f", 
                str(self.base_dir/"logging/elk/docker-compose.yml"), 
                "up", "-d" 
            ], cwd=self.base_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Compile + run syscall hook
            subprocess.run([ 
                "gcc", "-o", str(self.base_dir/"syscall_hooks/linux/syscall_hook"),
                str(self.base_dir/"syscall_hooks/linux/syscall_hook.c")
            ], cwd=self.base_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            p = subprocess.Popen([str(self.base_dir/"syscall_hooks/linux/syscall_hook"), "/usr/sbin/sshd"],
                                 cwd=self.base_dir)
            self.processes["syscall_hook"] = p
            self._log_event("syscall", f"Started syscall hook, logging → {self.log_paths['syscall']}")

            # Threat intel thread
            self.running = True
            t = threading.Thread(target=self._monitor_threats, daemon=True)
            t.start()
            self.processes["threat_intel"] = t
            self._log_event("threat_intel", f"Threat-Intel monitor started, logging → {self.log_paths['threat_intel']}")

            self.log_queue.put("Services started — compiling logs in ./logging/")
            return True
        except Exception as e:
            self.log_queue.put(f"Error starting: {e}")
            return False

    def _monitor_threats(self):
        while self.running:
            time.sleep(30)
            # simulate a threat check entry
            self._log_event("threat_intel", f"Threat check at {time.strftime('%H:%M:%S')}")
            self.log_queue.put("Threat intel check logged")

    def stop_services(self):
        self.running = False
        for name, p in self.processes.items():
            if hasattr(p, "terminate"):
                p.terminate()
        subprocess.run([ 
            "docker-compose", "-f",
            str(self.base_dir/"honeypots/cowrie/docker-compose.yml"),
            "down"
        ], cwd=self.base_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.log_queue.put("All services stopped")

    def _log_event(self, category, message):
        """Append a timestamped line to the appropriate log file."""
        path = self.log_paths[category]
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        line = f'{{"timestamp":"{ts}","event":"{message}"}}\n'
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a") as f:
                f.write(line)
        except PermissionError:
            # if we cannot write to /var/log/... just queue an error
            self.log_queue.put(f"Permission denied writing {path}")

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(HONEY["title"], curses.COLOR_YELLOW, -1)
    curses.init_pair(HONEY["menu"], curses.COLOR_MAGENTA, -1)
    curses.init_pair(HONEY["status_running"], curses.COLOR_GREEN, -1)
    curses.init_pair(HONEY["status_stopped"], curses.COLOR_RED, -1)
    curses.init_pair(HONEY["box"], curses.COLOR_CYAN, -1)
    curses.init_pair(HONEY["text"], curses.COLOR_WHITE, -1)

def draw_box(stdscr, y, x, h, w, title):
    """Draw a bordered box and title, clipped to screen."""
    max_y, max_x = stdscr.getmaxyx()
    if y+h > max_y or x+w > max_x:
        return
    win = stdscr.subwin(h, w, y, x)
    win.attron(curses.color_pair(HONEY["box"]))
    win.box()
    win.addstr(0, 2, f" {title} ")
    win.attroff(curses.color_pair(HONEY["box"]))
    return win

def draw_log_status(stdscr, manager, y, category, width):
    """In the box for `category`, show full path and last 2 logs."""
    path = manager.log_paths[category]
    exists = path.exists()
    win = draw_box(stdscr, y, 2, 5, width, category.capitalize() + " Logs")
    if not win:
        return
    text_col = curses.color_pair(HONEY["text"])
    win.attron(text_col)
    win.addstr(1, 2, f"Path: {str(path)}")
    status = "It exists" if exists else "Is missing"
    win.addstr(2, 2, f"Status: {status}")
    if exists:
        try:
            lines = open(path).read().splitlines()[-2:]
        except Exception:
            lines = ["<unable to read>"]
        for i, L in enumerate(lines):
            win.addstr(3+i, 2, L[:width-4])
    win.attroff(text_col)


def draw_menu(stdscr, manager, status):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    # Title
    title = "🐝 BLACKHOLE NEXUS HONEYPOT CONTROLLER 🍯"
    stdscr.attron(curses.color_pair(HONEY["title"]) | curses.A_BOLD)
    stdscr.addstr(1, max(0, (w - len(title)) // 2), title)
    stdscr.attroff(curses.color_pair(HONEY["title"]) | curses.A_BOLD)

    # Status line
    col = HONEY["status_running"] if status == "Running" else HONEY["status_stopped"]
    stdscr.attron(curses.color_pair(col))
    stdscr.addstr(3, 2, f"Status: {status}")
    stdscr.attroff(curses.color_pair(col))

    # Corrected log-status calls
    draw_log_status(stdscr, manager, 5, "cowrie", w - 4)
    draw_log_status(stdscr, manager, 11, "syscall", w - 4)
    draw_log_status(stdscr, manager, 17, "threat_intel", w - 4)

    # Menu
    stdscr.attron(curses.color_pair(HONEY["menu"]))
    menu = ["1.Start services", "2.Stop services", "3.View live Cowrie", "4.Generate report", "Q.Quit"]
    for i, item in enumerate(menu):
        stdscr.addstr(24 + i, 2, item)
    stdscr.attroff(curses.color_pair(HONEY["menu"]))
    stdscr.refresh()


def main(stdscr):
    curses.curs_set(0)
    init_colors()
    mgr = HoneypotManager()
    status="Stopped"
    while True:
        draw_menu(stdscr, mgr, status)
        c = stdscr.getch()
        if c==ord('1'):
            if mgr.start_services(): status="Running"
        elif c==ord('2'):
            mgr.stop_services(); status="Stopped"
        elif c==ord('3'):
            # live cowrie
            p = mgr.log_paths["cowrie"]
            if p.exists():
                curses.endwin()  # End curses mode before running subprocess
                try:
                    # Run tail -f in non-blocking mode
                    subprocess.Popen(["tail", "-f", str(p)])
                    # Return to curses mode
                    stdscr.clear()
                    stdscr.refresh()
                except Exception as e:
                    mgr.log_queue.put(f"Error displaying log: {str(e)}")
            else:
                mgr.log_queue.put(f"Cowrie log missing")
        elif c == ord('q'):  # Quit when q is pressed
            break

if __name__=="__main__":
    curses.wrapper(main)
