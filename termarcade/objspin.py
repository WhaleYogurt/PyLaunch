import json
import math
import os
import shutil
import sys
import time

from .app import move_home, clear_screen, hide_cursor, show_cursor
from .input import poll_key

SHADES = " .:-=+*#%@"
CACHE_VERSION = 1
MIN_COLS = 80
MIN_ROWS = 24


def load_obj_wireframe(path: str):
    """Load OBJ and return (vertices, edges) for wireframe rendering."""
    verts = []
    faces = []
    explicit_edges = set()

    def decode_index(token: str):
        head = token.split("/")[0]
        if not head:
            return None
        try:
            idx = int(head)
        except ValueError:
            return None
        if idx == 0:
            return None
        if idx < 0:
            idx = len(verts) + 1 + idx
        else:
            idx -= 1
        return idx if 0 <= idx < len(verts) else None

    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for raw in handle:
            if not raw or raw[0] in "#\n\r":
                continue
            parts = raw.strip().split()
            if not parts:
                continue
            tag = parts[0]
            if tag == "v" and len(parts) >= 4:
                try:
                    x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                except ValueError:
                    continue
                verts.append((x, y, z))
            elif tag == "f" and len(parts) >= 4:
                idxs = []
                for token in parts[1:]:
                    vi = decode_index(token)
                    if vi is not None:
                        idxs.append(vi)
                if len(idxs) >= 2:
                    faces.append(idxs)
            elif tag == "l" and len(parts) >= 3:
                prev = None
                for token in parts[1:]:
                    vi = decode_index(token)
                    if vi is None:
                        prev = None
                        continue
                    if prev is not None and vi != prev:
                        a, b = (prev, vi) if prev < vi else (vi, prev)
                        explicit_edges.add((a, b))
                    prev = vi
    edges = set(explicit_edges)
    for face in faces:
        for a, b in zip(face, face[1:]):
            i, j = (a, b) if a < b else (b, a)
            edges.add((i, j))
        if len(face) > 2:
            a, b = face[-1], face[0]
            i, j = (a, b) if a < b else (b, a)
            edges.add((i, j))
    if not verts:
        raise RuntimeError("No vertices in OBJ")
    return verts, list(edges)


def normalize(verts):
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    cx = (min(xs) + max(xs)) * 0.5
    cy = (min(ys) + max(ys)) * 0.5
    cz = (min(zs) + max(zs)) * 0.5
    centered = [(x - cx, y - cy, z - cz) for (x, y, z) in verts]
    r = max((x * x + y * y + z * z) ** 0.5 for (x, y, z) in centered) or 1.0
    s = 2.2 / r
    return [(x * s, y * s, z * s) for (x, y, z) in centered]


def rot_y(point, angle):
    x, y, z = point
    ca, sa = math.cos(angle), math.sin(angle)
    return (ca * x + sa * z, y, -sa * x + ca * z)


def project(point, fov, cam_d):
    x, y, z = point
    zc = z + cam_d
    if zc <= 1e-3:
        zc = 1e-3
    k = fov / zc
    return (x * k, y * k, z)


def draw_line(buf, zbuf, p0, p1, w, h, z_to_char):
    (x0, y0, z0) = p0
    (x1, y1, z1) = p1
    steps = int(max(8, min(600, max(abs(x1 - x0), abs(y1 - y0)) * 1.6)))
    for i in range(steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        z = z0 + (z1 - z0) * t
        ix, iy = int(round(x)), int(round(y))
        if 0 <= ix < w and 0 <= iy < h and z > zbuf[iy][ix]:
            zbuf[iy][ix] = z
            buf[iy][ix] = z_to_char(z)


def buffer_to_string(buf):
    return "\n".join("".join(row) for row in buf)


def compute_bbox_union(buffers):
    min_r = min_c = 10**9
    max_r = max_c = -10**9
    for buf in buffers:
        h = len(buf)
        w = len(buf[0]) if h else 0
        for r in range(h):
            row = buf[r]
            for c in range(w):
                if row[c] != " ":
                    if r < min_r:
                        min_r = r
                    if r > max_r:
                        max_r = r
                    if c < min_c:
                        min_c = c
                    if c > max_c:
                        max_c = c
    if max_r < min_r or max_c < min_c:
        return (0, 0, 0, 0)
    return (min_r, max_r, min_c, max_c)


def crop(buf, bbox):
    a, b, c, d = bbox
    return [row[c : d + 1] for row in buf[a : b + 1]]


class OBJSpinner:
    """
    OBJSpinner
    ----------
    Build and cache ASCII frames for a horizontally spinning OBJ model.
    - Provide `obj_path` or use built-in Lambda.
    - Call build_if_needed(), then playback().
    Cache file: <obj_path>.cache.json (side-by-side with the obj).
    """

    def __init__(self, obj_path: str | None = None, aspect: float = 0.5, frames: int = 144):
        self.obj_path = obj_path or self._default_lambda_path()
        self.aspect = self._validate_aspect(aspect)
        self.frames = self._validate_frames(frames)
        self.cache_path = self._default_cache_path()

    def _default_lambda_path(self) -> str:
        here = os.path.dirname(__file__)
        return os.path.join(here, "assets", "lambda.obj")

    def _default_cache_path(self) -> str:
        return f"{self.obj_path}.cache.json"

    @staticmethod
    def _validate_frames(value: int) -> int:
        if not isinstance(value, int):
            raise ValueError("frames must be an integer")
        if value <= 0:
            raise ValueError("frames must be a positive integer")
        return value

    @staticmethod
    def _validate_aspect(value: float) -> float:
        try:
            aspect = float(value)
        except (TypeError, ValueError):
            raise ValueError("aspect must be numeric") from None
        if aspect <= 0:
            raise ValueError("aspect must be greater than zero")
        return aspect

    def _render_buffer(self, angle, size, verts, edges):
        cols, rows = size
        w, h = cols, rows
        buf = [[" " for _ in range(w)] for _ in range(h)]
        zbuf = [[-1e9 for _ in range(w)] for _ in range(h)]
        fov = min(w, h) * 0.98
        cam_d = 4.0
        scale = 1.0
        rverts = [rot_y(v, angle) for v in verts]
        projected = [project(v, fov, cam_d) for v in rverts]
        zs = [pz for _, _, pz in projected]
        zmin, zmax = (min(zs), max(zs)) if zs else (0.0, 1.0)
        if zmax - zmin < 1e-6:
            zmax = zmin + 1e-6

        def z_to_char(z):
            t = (z - zmin) / (zmax - zmin)
            t = 0.0 if t < 0 else (1.0 if t > 1 else t)
            return SHADES[int(t * (len(SHADES) - 1))]

        screen = []
        for (px, py, pz) in projected:
            sx = int(w * 0.5 + px * scale)
            sy = int(h * 0.5 - py * scale * self.aspect)
            screen.append((sx, sy, pz))
        for (i, j) in edges:
            (sx0, sy0, z0) = screen[i]
            (sx1, sy1, z1) = screen[j]
            draw_line(buf, zbuf, (sx0, sy0, z0), (sx1, sy1, z1), w, h, z_to_char)
        return buf

    def _build_cache(self, cols, rows, signature):
        verts, edges = load_obj_wireframe(self.obj_path)
        verts = normalize(verts)
        bufs = []
        for i in range(self.frames):
            ang = (2.0 * math.pi) * (i / self.frames)
            bufs.append(self._render_buffer(ang, (cols, rows), verts, edges))
        bbox = compute_bbox_union(bufs)
        frames = [buffer_to_string(crop(b, bbox)) for b in bufs]
        payload = {
            "frames": frames,
            "width": len(frames[0].split("\n")[0]) if frames else 0,
            "height": len(frames[0].split("\n")) if frames else 0,
            "version": CACHE_VERSION,
            "params": {
                "frames": self.frames,
                "aspect": self.aspect,
                "cols": cols,
                "rows": rows,
                "obj_signature": signature,
            },
        }
        self._write_cache(payload)
        return payload

    def _write_cache(self, payload):
        tmp_path = self.cache_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        os.replace(tmp_path, self.cache_path)

    def _load_cache(self):
        try:
            with open(self.cache_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except FileNotFoundError:
            return None
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(data, dict):
            return None
        if data.get("version") != CACHE_VERSION:
            return None
        return data

    def _obj_signature(self):
        try:
            stat = os.stat(self.obj_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"OBJ not found: {self.obj_path}") from None
        return {"mtime": stat.st_mtime, "size": stat.st_size}

    def _cache_matches(self, payload, cols, rows, signature):
        params = payload.get("params") or {}
        return (
            params.get("frames") == self.frames
            and params.get("aspect") == self.aspect
            and params.get("cols") == cols
            and params.get("rows") == rows
            and params.get("obj_signature") == signature
        )

    def _resolve_dims(self, cols, rows):
        if cols is None or rows is None:
            cols, rows = shutil.get_terminal_size((120, 36))
        try:
            cols = int(cols)
            rows = int(rows)
        except (TypeError, ValueError):
            raise ValueError("cols and rows must be integers") from None
        if cols <= 0 or rows <= 0:
            raise ValueError("cols and rows must be positive")
        return max(MIN_COLS, cols), max(MIN_ROWS, rows)

    def build_if_needed(self, cols: int | None = None, rows: int | None = None, force: bool = False):
        cols, rows = self._resolve_dims(cols, rows)
        signature = self._obj_signature()
        if not force:
            cached = self._load_cache()
            if cached and self._cache_matches(cached, cols, rows, signature):
                return cached
        return self._build_cache(cols, rows, signature)

    def playback(self, fps: float = 30.0, on_key=None):
        data = self.build_if_needed()
        frames = data.get("frames") or []
        if not frames:
            raise RuntimeError("Spinner cache contains no frames")
        dt = 1.0 / max(1.0, fps)
        idx = 0
        try:
            hide_cursor()
            clear_screen()
            while True:
                move_home()
                sys.stdout.write(frames[idx])
                sys.stdout.flush()
                key = poll_key()
                if key is not None and on_key:
                    if on_key(key) is False:
                        break
                idx = (idx + 1) % len(frames)
                time.sleep(dt)
        finally:
            show_cursor()
