# Getting Started

Install locally (dev mode):

```bash
git clone https://github.com/yourname/termarcade.git
cd termarcade
pip install -e .
Run the spinner launcher:

bash
Copy code
python scripts/launcher.py                         # built-in Lambda
python scripts/launcher.py path/to/model.obj       # custom OBJ
python scripts/launcher.py --rebuild path/to.obj   # force rebuild
Run the Snake example:

bash
Copy code
python examples/snake/snake.py
pgsql
Copy code

---

# termarcade_repo/docs/TerminalApp.md
```markdown
# TerminalApp & MenuWidget

`TerminalApp` drives a simple render/update/input loop you fully control.

```python
from termarcade.app import TerminalApp, MenuWidget

app = TerminalApp(title="My App")
menu = MenuWidget(items=["Start", "Exit"])

def on_key(ctx, key):
    if key == "UP": menu.move(-1)
    elif key == "DOWN": menu.move(+1)
    elif key == "ENTER":
        if menu.current_label() == "Exit":
            ctx.request_exit()

def on_render(ctx, write):
    write("=== My App ===")
    for line in menu.render_lines(ctx.width):
        write(line)

app.run(state={}, menu=menu, on_key=on_key, on_render=on_render, on_update=None, fps=30)
write(line) pads each line to the terminal width for stable redraws.

ctx.state is your mutable dict for sharing state.

MenuWidget is optional; you can render anything you like.

yaml
Copy code

---

# termarcade_repo/docs/OBJSpinner.md
```markdown
# OBJSpinner

Cache and play a horizontally spinning ASCII view of any `.obj` file.

```python
from termarcade.objspin import OBJSpinner

spinner = OBJSpinner(obj_path="path/to/model.obj", aspect=0.5, frames=144)
spinner.build_if_needed(force=False)   # builds <model>.obj.cache.json next to your OBJ
spinner.playback(fps=30.0)             # streams cached frames to the terminal
Default Lambda
If you do not pass an obj_path, the built-in Lambda model is used:

bash
Copy code
termarcade/assets/lambda.obj
How it works
Renders a full 360° rotation

Computes a global bounding box so no characters get clipped

Crops every frame to that box

Saves frames as a JSON cache with build metadata next to your OBJ for fast playback and validation

yaml
Copy code

---
