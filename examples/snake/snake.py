#!/usr/bin/env python3
"""
Snake demo using termarcade.
Choose difficulty and play a simple terminal Snake.
"""
import random
from termarcade.app import TerminalApp, MenuWidget, Context
from termarcade.input import Keys

def run():
    app = TerminalApp(title="Arcade")
    state = {
        "screen":"choose_game",
        "difficulty":"Normal",
        "speed_map":{"Easy":6,"Normal":10,"Hard":14,"Insane":18},
        "snake":None
    }
    menu_game = MenuWidget(items=["Snake Classic","Exit"])
    menu_diff = MenuWidget(items=["Easy","Normal","Hard","Insane","Back"])

    def snake_reset(ctx: Context):
        w,h = ctx.width, ctx.height
        gw = max(20, min(60, w-4)); gh = max(12, min(24, h-6))
        cx, cy = gw//2, gh//2
        s={"grid_w":gw,"grid_h":gh,"dir":(1,0),
           "body":[(cx-2,cy),(cx-1,cy),(cx,cy)],"grow":0,
           "food":None,"accum":0.0,"alive":True,"score":0}
        def spawn():
            allc=[(x,y) for y in range(s["grid_h"]) for x in range(s["grid_w"])]
            occ=set(s["body"]); free=[p for p in allc if p not in occ]; return random.choice(free) if free else (0,0)
        s["food"]=spawn(); s["spawn"]=spawn; state["snake"]=s

    def on_key(ctx: Context, key: str):
        scr=state["screen"]
        if scr=="choose_game":
            if key==Keys.UP: menu_game.move(-1)
            elif key==Keys.DOWN: menu_game.move(+1)
            elif key==Keys.ENTER:
                c=menu_game.current_label()
                if c=="Exit": ctx.request_exit()
                else: state["screen"]="choose_difficulty"
        elif scr=="choose_difficulty":
            if key==Keys.UP: menu_diff.move(-1)
            elif key==Keys.DOWN: menu_diff.move(+1)
            elif key==Keys.ENTER:
                c=menu_diff.current_label()
                if c=="Back": state["screen"]="choose_game"
                else:
                    state["difficulty"]=c; snake_reset(ctx); state["screen"]="snake"
        elif scr=="snake":
            s=state["snake"]; 
            if not s or not s["alive"]:
                if key in (Keys.ENTER, 'q','Q'): state["screen"]="choose_game"; return
            if key in ('q','Q'): state["screen"]="choose_game"; return
            dx,dy = s["dir"]
            if key==Keys.LEFT and dx!=1: s["dir"]=(-1,0)
            if key==Keys.RIGHT and dx!=-1: s["dir"]=(1,0)
            if key==Keys.UP and dy!=1: s["dir"]=(0,-1)
            if key==Keys.DOWN and dy!=-1: s["dir"]=(0,1)

    def on_update(ctx: Context, dt: float):
        if state["screen"]!="snake": return
        s=state["snake"]; 
        if not s or not s["alive"]: return
        tps=state["speed_map"][state["difficulty"]]; s["accum"]+=dt; step=1.0/tps
        while s["accum"]>=step:
            s["accum"]-=step
            (dx,dy)=s["dir"]; hx,hy=s["body"][-1]; nx,ny=hx+dx, hy+dy
            if nx<0 or nx>=s["grid_w"] or ny<0 or ny>=s["grid_h"] or (nx,ny) in s["body"]:
                s["alive"]=False; break
            s["body"].append((nx,ny))
            if (nx,ny)==s["food"]:
                s["score"]+=1; s["grow"]+=2; s["food"]=s["spawn"]()
            if s["grow"]>0: s["grow"]-=1
            else: s["body"].pop(0)

    def on_render(ctx: Context, write):
        write("Arcade — Snake")
        write("↑/↓ move • Enter select • Esc quit • Q quit game")
        write("")
        if state["screen"]=="choose_game":
            write("Choose a game:"); write("")
            for line in menu_game.render_lines(ctx.width): write(line)
        elif state["screen"]=="choose_difficulty":
            write("Choose difficulty:"); write(f"Current game: Snake Classic")
            write("")
            for line in menu_diff.render_lines(ctx.width): write(line)
        elif state["screen"]=="snake":
            s=state["snake"]; 
            if not s: write("Initializing…"); return
            gw,gh=s["grid_w"], s["grid_h"]; left=max(0,(ctx.width-(gw+2))//2); pad=" "*left
            info=f"Difficulty: {state['difficulty']}   Score: {s['score']}"; write(info); write("")
            write(pad+"+"+"-"*gw+"+")
            snake_set=set(s["body"]); food=s["food"]
            for y in range(gh):
                row=["|"]
                for x in range(gw):
                    if (x,y)==s["body"][-1]: row.append("@")
                    elif (x,y) in snake_set: row.append("o")
                    elif (x,y)==food: row.append("*")
                    else: row.append(" ")
                row.append("|"); write(pad+"".join(row))
            write(pad+"+"+"-"*gw+"+")
            if s["alive"]: write("Use arrows. Q to quit to menu.")
            else: write("Game Over! Enter to return.")

    app.run(state={}, menu=menu_game, on_key=on_key, on_render=on_render, on_update=on_update, fps=30)

if __name__ == "__main__":
    run()
