import re

ESC = "\x1b"

def ansi(*codes: int) -> str:
    return f"\x1b[{';'.join(str(c) for c in codes)}m" if codes else ""

RESET = ansi(0)
BOLD  = ansi(1)
DIM   = ansi(2)
INV   = ansi(7)

class FG:
    BLACK=30; RED=31; GREEN=32; YELLOW=33; BLUE=34; MAGENTA=35; CYAN=36; WHITE=37
    BRIGHT_BLACK=90; BRIGHT_RED=91; BRIGHT_GREEN=92; BRIGHT_YELLOW=93
    BRIGHT_BLUE=94; BRIGHT_MAGENTA=95; BRIGHT_CYAN=96; BRIGHT_WHITE=97

class BG:
    BLACK=40; RED=41; GREEN=42; YELLOW=43; BLUE=44; MAGENTA=45; CYAN=46; WHITE=47
    BRIGHT_BLACK=100; BRIGHT_RED=101; BRIGHT_GREEN=102; BRIGHT_YELLOW=103
    BRIGHT_BLUE=104; BRIGHT_MAGENTA=105; BRIGHT_CYAN=106; BRIGHT_WHITE=107

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

def style(text: str, fg: int|None=None, bg: int|None=None,
          bold: bool=False, dim: bool=False, invert: bool=False) -> str:
    codes = []
    if bold:  codes.append(1)
    if dim:   codes.append(2)
    if invert:codes.append(7)
    if fg is not None: codes.append(fg)
    if bg is not None: codes.append(bg)
    return (ansi(*codes) + text + RESET) if codes else text

def visible_len(s: str) -> int:
    return len(ANSI_RE.sub("", s))

def safe_pad(s: str, width: int) -> str:
    v = visible_len(s)
    return s + " " * max(0, width - v)

def safe_truncate(s: str, width: int) -> str:
    """Truncate to width in visible characters, preserving ANSI codes."""
    out = []
    vis = 0
    i = 0
    while i < len(s) and vis < width:
        if s[i] == "\x1b" and i+1 < len(s) and s[i+1] == "[":
            j = i+2
            while j < len(s) and s[j] != "m":
                j += 1
            j = min(j+1, len(s))
            out.append(s[i:j])
            i = j
        else:
            out.append(s[i])
            vis += 1
            i += 1
    return "".join(out)

def fit_line(s: str, width: int) -> str:
    return safe_pad(safe_truncate(s, width), width)
