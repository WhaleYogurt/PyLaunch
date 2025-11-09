# TerminalApp & MenuWidget

`TerminalApp` owns the render/update/input loop. Provide three callbacks:

- `on_render(ctx, write)` – emit text via `write(str)`; each line is padded to
  the terminal width so shrinking UIs no longer leave stale rows behind.
- `on_key(ctx, key)` – react to printable characters or the symbols in
  `termarcade.input.Keys`.
- `on_update(ctx, dt)` – optional; advance simulation using the frame delta.

Pass a `state` dict if you need shared mutable state. The dict is used as-is, so
you can capture it outside the app and observe mutations after `run` exits.

```python
from termarcade.app import TerminalApp, MenuWidget
from termarcade.input import Keys

menu = MenuWidget(["Play", "Quit"])
state = {"screen": "menu"}

def on_key(ctx, key):
    if key == Keys.UP:
        menu.move(-1)
    elif key == Keys.DOWN:
        menu.move(+1)
    elif key == Keys.ENTER and menu.current_label() == "Quit":
        ctx.request_exit()

def on_render(ctx, write):
    write("Demo")
    write("")
    for line in menu.render_lines(ctx.width):
        write(line)

TerminalApp(title="Demo").run(state=state, menu=menu,
                              on_key=on_key, on_render=on_render,
                              on_update=None, fps=30)
```
