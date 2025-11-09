import json
import tempfile
import unittest
from pathlib import Path

from termarcade.objspin import OBJSpinner, load_obj_wireframe


class ObjSpinTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.model_path = Path(self.tmp.name) / "model.obj"
        self.model_path.write_text(
            "\n".join(
                [
                    "v 0 0 0",
                    "v 1 0 0",
                    "v 0 1 0",
                    "l 1 2 3",
                ]
            ),
            encoding="utf-8",
        )

    def test_cache_rebuilds_when_frames_change(self):
        spinner = OBJSpinner(obj_path=str(self.model_path), frames=2)
        data = spinner.build_if_needed(cols=120, rows=40, force=True)
        self.assertEqual(len(data["frames"]), 2)
        cache_contents = json.loads(Path(spinner.cache_path).read_text(encoding="utf-8"))
        self.assertEqual(cache_contents["params"]["cols"], 120)
        self.assertEqual(cache_contents["params"]["rows"], 40)

        spinner_updated = OBJSpinner(obj_path=str(self.model_path), frames=3)
        data_updated = spinner_updated.build_if_needed(cols=120, rows=40)
        self.assertEqual(len(data_updated["frames"]), 3)

    def test_loads_line_records_with_slashes(self):
        path = Path(self.tmp.name) / "slashes.obj"
        path.write_text(
            "\n".join(
                [
                    "v 0 0 0",
                    "v 1 0 0",
                    "v 0 1 0",
                    "l 1/1/1 2/2/2 3/3/3",
                ]
            ),
            encoding="utf-8",
        )
        verts, edges = load_obj_wireframe(str(path))
        self.assertEqual(len(verts), 3)
        self.assertTrue(edges)

    def test_invalid_frame_count_rejected(self):
        with self.assertRaises(ValueError):
            OBJSpinner(obj_path=str(self.model_path), frames=0)


if __name__ == "__main__":
    unittest.main()
