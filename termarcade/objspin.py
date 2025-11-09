import os, sys, math, pickle, shutil, time
from typing import List, Tuple
from .app import move_home, clear_screen, hide_cursor, show_cursor
from .input import Keys, poll_key

SHADES = " .:-=+*#%@"

def load_obj_wireframe(path: str):
    """Load OBJ and return (vertices, edges) for wireframe."""
    verts=[]; faces=[]; lines=[]
    with open(path,"r",encoding="utf-8",errors="ignore") as f:
        for raw in f:
            if not raw or raw[0] in "#\n\r": continue
            parts = raw.strip().split()
            if not parts: continue
            tag = parts[0]
            if tag=="v" and len(parts)>=4:
                try:
                    x,y,z = float(parts[1]), float(parts[2]), float(parts[3])
                    verts.append((x,y,z))
                except: pass
            elif tag=="f" and len(parts)>=4:
                idxs=[]
                for tok in parts[1:]:
                    i = tok.split("/")[0]
                    if i:
                        vi = int(i)
                        if vi<0: vi = len(verts)+1+vi
                        idxs.append(vi-1)
                if len(idxs)>=2: faces.append(idxs)
            elif tag=="l" and len(parts)>=3:
                idxs=[]
                for tok in parts[1:]:
                    vi=int(tok)
                    if vi<0: vi = len(verts)+1+vi
                    idxs.append(vi-1)
                for a,b in zip(idxs, idxs[1:]):
                    lines.append((a,b))
    edges=set(lines)
    for face in faces:
        for a,b in zip(face, face[1:]):
            i,j = (a,b) if a<b else (b,a); edges.add((i,j))
        if len(face)>2:
            a,b=face[-1], face[0]; i,j=(a,b) if a<b else (b,a); edges.add((i,j))
    if not verts: raise RuntimeError("No vertices in OBJ")
    return verts, list(edges)

def normalize(verts):
    xs=[v[0] for v in verts]; ys=[v[1] for v in verts]; zs=[v[2] for v in verts]
    cx=(min(xs)+max(xs))*0.5; cy=(min(ys)+max(ys))*0.5; cz=(min(zs)+max(zs))*0.5
    centered=[(x-cx,y-cy,z-cz) for (x,y,z) in verts]
    r=max((x*x+y*y+z*z)**0.5 for (x,y,z) in centered) or 1.0
    s=2.2/r
    return [(x*s,y*s,z*s) for (x,y,z) in centered]

def rot_y(p,a):
    x,y,z=p; ca,sa=math.cos(a),math.sin(a)
    return (ca*x+sa*z, y, -sa*x+ca*z)

def project(p, fov, cam_d):
    x,y,z=p; zc=z+cam_d
    if zc<=1e-3: zc=1e-3
    k=fov/zc
    return (x*k, y*k, z)

def draw_line(buf, zbuf, p0, p1, w, h, z_to_char):
    (x0,y0,z0)=p0; (x1,y1,z1)=p1
    steps=int(max(8, min(600, max(abs(x1-x0), abs(y1-y0))*1.6)))
    for i in range(steps+1):
        t=i/steps; x=x0+(x1-x0)*t; y=y0+(y1-y0)*t; z=z0+(z1-z0)*t
        ix,iy=int(round(x)), int(round(y))
        if 0<=ix<w and 0<=iy<h and z>zbuf[iy][ix]:
            zbuf[iy][ix]=z; buf[iy][ix]=z_to_char(z)

def buffer_to_string(buf): return "\n".join("".join(row) for row in buf)

def compute_bbox_union(buffers):
    min_r=min_c=10**9; max_r=max_c=-10**9
    for buf in buffers:
        h=len(buf); w=len(buf[0]) if h else 0
        for r in range(h):
            row=buf[r]
            for c in range(w):
                if row[c]!=" ":
                    if r<min_r:min_r=r
                    if r>max_r:max_r=r
                    if c<min_c:min_c=c
                    if c>max_c:max_c=c
    if max_r<min_r or max_c<min_c: return (0,0,0,0)
    return (min_r,max_r,min_c,max_c)

def crop(buf,bbox):
    a,b,c,d=bbox
    return [row[c:d+1] for row in buf[a:b+1]]

class OBJSpinner:
    """
    OBJSpinner
    ----------
    Build and cache ASCII frames for a horizontally spinning OBJ model.
    - Provide `obj_path` or use built-in Lambda.
    - Call build_if_needed(), then playback().
    Cache file: <obj_path>.pkl (side-by-side with the obj).
    """
    def __init__(self, obj_path: str|None=None, aspect: float=0.5, frames:int=144):
        self.obj_path = obj_path or self._default_lambda_path()
        self.aspect = aspect
        self.frames = frames
        self.cache_path = self.obj_path + ".pkl"

    def _default_lambda_path(self)->str:
        here = os.path.dirname(__file__)
        return os.path.join(here, "assets", "lambda.obj")

    def _render_buffer(self, angle, size, verts, edges):
        cols, rows = size; w,h=cols, rows
        buf=[[" " for _ in range(w)] for _ in range(h)]
        zbuf=[[-1e9 for _ in range(w)] for _ in range(h)]
        fov = min(w,h)*0.98; cam_d=4.0; scale=1.0
        rverts=[rot_y(v, angle) for v in verts]
        projected=[project(v,fov,cam_d) for v in rverts]
        zs=[pz for _,_,pz in projected]; zmin, zmax = (min(zs), max(zs)) if zs else (0.0,1.0)
        if zmax - zmin < 1e-6: zmax = zmin + 1e-6
        def z_to_char(z):
            t=(z-zmin)/(zmax-zmin); t=0.0 if t<0 else (1.0 if t>1 else t)
            return SHADES[int(t*(len(SHADES)-1))]
        screen=[]
        for (px,py,pz) in projected:
            sx=int(w*0.5 + px*scale)
            sy=int(h*0.5 - py*scale*self.aspect)
            screen.append((sx,sy,pz))
        for (i,j) in edges:
            (sx0,sy0,z0)=screen[i]; (sx1,sy1,z1)=screen[j]
            draw_line(buf,zbuf,(sx0,sy0,z0),(sx1,sy1,z1),w,h,z_to_char)
        return buf

    def _build_cache(self, cols, rows):
        verts, edges = load_obj_wireframe(self.obj_path)
        verts = normalize(verts)
        bufs=[]
        for i in range(self.frames):
            ang = (2.0*math.pi)*(i/self.frames)
            bufs.append(self._render_buffer(ang, (cols, rows), verts, edges))
        bbox = compute_bbox_union(bufs)
        frames = [buffer_to_string(crop(b, bbox)) for b in bufs]
        payload = {"frames": frames,
                   "width": len(frames[0].split("\n")[0]) if frames else 0,
                   "height": len(frames[0].split("\n")) if frames else 0}
        with open(self.cache_path, "wb") as f:
            pickle.dump(payload, f)
        return payload

    def build_if_needed(self, cols: int|None=None, rows: int|None=None, force: bool=False):
        if not cols or not rows:
            cols, rows = shutil.get_terminal_size((120, 36))
            cols=max(80, cols); rows=max(24, rows)
        if force or not os.path.exists(self.cache_path):
            return self._build_cache(cols, rows)
        with open(self.cache_path, "rb") as f:
            return pickle.load(f)

    def playback(self, fps: float=30.0, on_key=None):
        data = self.build_if_needed()
        frames=data["frames"]; fw=data["width"]; fh=data["height"]
        dt=1.0/fps; idx=0
        try:
            hide_cursor(); clear_screen()
            while True:
                move_home(); sys.stdout.write(frames[idx]); sys.stdout.flush()
                key = poll_key()
                if key is not None and on_key:
                    if on_key(key) is False: break
                idx=(idx+1)%len(frames); time.sleep(dt)
        finally:
            show_cursor()
