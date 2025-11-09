import unittest

from termarcade.ansi import RESET, ansi, safe_truncate


class AnsiTests(unittest.TestCase):
    def test_safe_truncate_preserves_reset(self):
        text = f"{ansi(31)}HELLO{RESET}"
        truncated = safe_truncate(text, 3)
        self.assertEqual(truncated, f"{ansi(31)}HEL{RESET}")

    def test_safe_truncate_plain_text(self):
        self.assertEqual(safe_truncate("ABCDE", 2), "AB")


if __name__ == "__main__":
    unittest.main()
