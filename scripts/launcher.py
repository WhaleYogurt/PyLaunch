#!/usr/bin/env python3
"""
OBJ spinner launcher.

Usage:
  python scripts/launcher.py                         # default lambda
  python scripts/launcher.py path/to/model.obj       # custom OBJ
  python scripts/launcher.py --rebuild path/to.obj   # force rebuild then play
"""
import sys, os
from termarcade.app import TerminalApp, MenuWidget
from termarcade.objspin import OBJSpinner

def main():
    obj_path = None
    force = False
    args = [a for a in sys.argv[1:] if a]
    if args and args[0] == "--rebuild":
        force = True
        args = args[1:]
    if args:
        obj_path = args[0]
        if not os.path.exists(obj_path):
            print("OBJ not found:", obj_path); return

    spinner = OBJSpinner(obj_path=obj_path, aspect=0.5)
    spinner.build_if_needed(force=force)

    app = TerminalApp(title="OBJ Spinner")
    menu = MenuWidget(items=["Play", "Rebuild Cache", "Exit"])
    state = {"playing": False}

    def on_key(ctx, key):
        if not state["playing"]:
            if key == "UP": menu.move(-1)
            elif key == "DOWN": menu.move(+1)
            elif key == "ENTER":
                choice = menu.current_label()
                if choice == "Play":
                    state["playing"] = True
                elif choice == "Rebuild Cache":
                    spinner.build_if_needed(force=True)
                elif choice == "Exit":
                    ctx.request_exit()
        else:
            if key == "ENTER":  # return to menu
                state["playing"] = False

    def on_render(ctx, write):
        if not state["playing"]:
            write("OBJ Spinner")
            write("↑/↓ move • Enter select • Esc quit")
            write("")
            for line in menu.render_lines(ctx.width):
                write(line)
            write("")
            p = spinner.obj_path
            write(f"Model: {p}")
            write(f"Cache: {spinner.cache_path}")
        else:
            write("Playing... Press Enter to return to menu.")
            def key_cb(k):
                return False if k == "ENTER" else True
            spinner.playback(fps=30.0, on_key=key_cb)
            state["playing"] = False

    app.run(state={}, menu=menu, on_key=on_key, on_render=on_render, on_update=None, fps=30)

if __name__ == "__main__":
    main()
