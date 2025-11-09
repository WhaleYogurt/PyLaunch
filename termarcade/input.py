import locale
import os, sys

IS_WINDOWS = os.name == "nt"
if IS_WINDOWS:
    import msvcrt
    def _read_windows_char():
        """Return the next keypress as a str, honoring the active console codepage."""
        if hasattr(msvcrt, "getwch"):
            try:
                return msvcrt.getwch()
            except Exception:
                pass
        encoding = sys.stdout.encoding or locale.getpreferredencoding(False) or "utf-8"
        try:
            return msvcrt.getch().decode(encoding, errors="ignore")
        except Exception:
            return ""
else:
    import termios, tty, select

class Keys:
    UP="UP"; DOWN="DOWN"; LEFT="LEFT"; RIGHT="RIGHT"; ENTER="ENTER"; ESC="ESC"

def poll_key():
    """Return one of Keys.* or a printable char, or None if no key."""
    if IS_WINDOWS:
        if not msvcrt.kbhit(): return None
        ch = _read_windows_char()
        if not ch: return None
        if ch in ("\x00", "\xe0"):
            code = _read_windows_char()
            mapping = {"H":Keys.UP, "P":Keys.DOWN, "K":Keys.LEFT, "M":Keys.RIGHT}
            return mapping.get(code)
        if ch in ("\r", "\n"): return Keys.ENTER
        if ch == "\x1b":       return Keys.ESC
        return ch if ch.isprintable() else None
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
