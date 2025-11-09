# OBJSpinner

`OBJSpinner` builds a cache of ASCII frames for any `.obj` and streams them to
the terminal. Pass a custom `obj_path`, or rely on the bundled `lambda.obj`.

```python
from termarcade.objspin import OBJSpinner

spinner = OBJSpinner(obj_path="assets/drone.obj", aspect=0.55, frames=180)
spinner.build_if_needed(force=False)  # creates assets/drone.obj.cache.json
spinner.playback(fps=30.0)
```

## Cache format

- Every OBJ stores its cache next to the source model as `<obj>.cache.json`.
- The cache is JSON (no pickle), so loading it cannot execute arbitrary code.
- Build metadata (aspect, frame count, terminal size, OBJ mtime/size) is stored
  inside the cache; if any of it changes, `build_if_needed` automatically
  rebuilds before playback.
- Use `spinner.build_if_needed(force=True)` to rebuild manually, or inspect the
  `spinner.cache_path` if you want to clean caches for distribution.

## Tips

- Keep `frames` modest (e.g., 120–180) when iterating so cache builds complete
  quickly; you can increase the value for a release build.
- Call `build_if_needed` ahead of time in CI or installation scripts so the
  first playback in production can rely on the cached frames.
