import os, sys

IS_WINDOWS = os.name == "nt"
if IS_WINDOWS:
    import msvcrt
else:
    import termios, tty, select

class Keys:
    UP="UP"; DOWN="DOWN"; LEFT="LEFT"; RIGHT="RIGHT"; ENTER="ENTER"; ESC="ESC"

def poll_key():
    """Return one of Keys.* or a printable char, or None if no key."""
    if IS_WINDOWS:
        if not msvcrt.kbhit(): return None
        b = msvcrt.getch()
        if b in (b"\x00", b"\xe0"):
            code = msvcrt.getch()
            return {b"H":Keys.UP, b"P":Keys.DOWN, b"K":Keys.LEFT, b"M":Keys.RIGHT}.get(code, None)
        if b in (b"\r", b"\n"): return Keys.ENTER
        if b == b"\x1b":        return Keys.ESC
        try:
            c = b.decode("utf-8", errors="ignore")
            return c if c and c.isprintable() else None
        except Exception:
            return None
    else:
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if not dr: return None
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            if select.select([sys.stdin], [], [], 0)[0] and sys.stdin.read(1) == "[":
                if select.select([sys.stdin], [], [], 0)[0]:
                    a = sys.stdin.read(1)
                    return {"A":Keys.UP,"B":Keys.DOWN,"C":Keys.RIGHT,"D":Keys.LEFT}.get(a, None)
            return Keys.ESC
        if ch in ("\r", "\n"): return Keys.ENTER
        return ch if ch.isprintable() else None
