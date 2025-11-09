import os, sys, time, shutil, signal
from dataclasses import dataclass
from typing import Callable, Optional, List
from .ansi import fit_line
from .input import poll_key, Keys

ESC = "\x1b"
def hide_cursor(): sys.stdout.write(f"{ESC}[?25l"); sys.stdout.flush()
def show_cursor(): sys.stdout.write(f"{ESC}[?25h"); sys.stdout.flush()
def clear_screen(): sys.stdout.write(f"{ESC}[2J{ESC}[H"); sys.stdout.flush()
def move_home(): sys.stdout.write(f"{ESC}[H"); sys.stdout.flush()

def get_size():
    try:
        cols, rows = shutil.get_terminal_size((100, 32))
    except Exception:
        cols, rows = 100, 32
    return cols, rows

IS_WINDOWS = os.name == "nt"
if not IS_WINDOWS:
    import termios, tty

@dataclass
class Context:
    width: int
    height: int
    state: dict
    menu: Optional["MenuWidget"]
    _exit: bool = False
    def request_exit(self): self._exit = True

class MenuWidget:
    def __init__(self, items: List[str], selected: int=0,
                 label_of=None, is_enabled=None, render_item=None):
        self.items=list(items); self.selected=selected
        self.label_of = label_of or (lambda x: str(x))
        self.is_enabled = is_enabled or (lambda _x: True)
        self.render_item = render_item or self._default_render
    def _default_render(self, label, i, selected, enabled):
        base = ("  "+label) if enabled else "  " + label
        return ("> "+label) if selected else base
    def move(self, d:int):
        if not self.items: return
        n=len(self.items)
        for _ in range(n):
            self.selected=(self.selected+d)%n
            if self.is_enabled(self.items[self.selected]): break
    def current(self): return self.items[self.selected] if self.items else None
    def current_label(self): return self.label_of(self.current()) if self.current() is not None else ""
    def render_lines(self, width:int)->List[str]:
        out=[]
        for i,item in enumerate(self.items):
            lbl=self.label_of(item); en=self.is_enabled(item)
            s=self.render_item(lbl,i,i==self.selected,en)
            out.append(fit_line(s, width))
        return out

class TerminalApp:
    def __init__(self, title="App"): self.title=title
    def run(self, state:dict|None, menu:MenuWidget|None,
            on_key:Callable, on_render:Callable, on_update:Callable|None=None, fps:int=30):
        state = state or {}
        ctx = Context(0,0,state,menu)
        if not IS_WINDOWS:
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        try:
            hide_cursor(); clear_screen()
            frame_dt = 1.0 / max(1, fps); last = time.perf_counter()
            while not ctx._exit:
                ctx.width, ctx.height = get_size()
                now = time.perf_counter(); dt = now - last; last = now
                if on_update: on_update(ctx, dt)
                lines=[]
                def write(s: str): lines.append(fit_line(s, ctx.width))
                on_render(ctx, write)
                move_home(); sys.stdout.write("\n".join(lines)); sys.stdout.flush()
                k = poll_key()
                if k is not None:
                    if k == Keys.ESC: ctx.request_exit()
                    else: on_key(ctx, k)
                time.sleep(max(0.0, frame_dt - (time.perf_counter()-now)))
        finally:
            if not IS_WINDOWS:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            show_cursor()
