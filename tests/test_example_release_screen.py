"""Permit the named public tutorial without opening arbitrary host paths."""
import unittest
import posixpath
import re
import tempfile
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

from scripts.build_trial import ROOT, __version__, build, reviewed_example_path, screen_content, snapshot, product_contents


class ExampleReleaseScreenTests(unittest.TestCase):
    def test_old_download_link_stops_build_before_creating_artifacts(self):
        read_bytes = Path.read_bytes
        def stale_entry(path):
            data = read_bytes(path)
            if path == ROOT / 'START_HERE.md':
                data = data.replace(('releases/tag/v' + __version__).encode(), b'releases/tag/v0.0.0rc1')
            return data
        with tempfile.TemporaryDirectory(prefix='taskcarry-download-guard-') as temporary:
            destination = Path(temporary) / 'product'
            with patch.object(Path, 'read_bytes', stale_entry):
                with self.assertRaisesRegex(RuntimeError, 'download entry must match'):
                    build(destination, profile='product')
            self.assertFalse(destination.exists())
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_missing_update_route_stops_build_before_creating_artifacts(self):
        read_bytes = Path.read_bytes
        def missing_route(path):
            data = read_bytes(path)
            if path == ROOT / 'START_HERE.md':
                data = data.replace(b'](docs/zh-TW/updating.md)', b'](docs/zh-TW/windows-example.md)')
            return data
        with tempfile.TemporaryDirectory(prefix='taskcarry-update-route-') as temporary:
            destination = Path(temporary) / 'product'
            with patch.object(Path, 'read_bytes', missing_route):
                with self.assertRaisesRegex(RuntimeError, 'both user routes'):
                    build(destination, profile='product')
            self.assertFalse(destination.exists())
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_product_document_links_resolve_inside_the_download(self):
        contents = product_contents(snapshot()[0])
        failures = []
        for name, data in contents.items():
            if not name.endswith(('.md', '.html')):
                continue
            text = data.decode('utf-8-sig')
            links = re.findall(r'\[[^\]]*\]\(([^)]+)\)', text)
            links += re.findall(r'(?:href|src)=[\"\x27]([^\"\x27]+)', text)
            for link in links:
                link = link.split(' "', 1)[0].strip('<>')
                parsed = urlsplit(link)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                target = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(parsed.path)))
                if target not in contents and not any(p.startswith(target.rstrip('/') + '/') for p in contents):
                    failures.append((name, link))
        self.assertEqual(failures, [], 'Downloaded user documentation must not link to excluded maintenance files')

    def test_only_named_tutorial_resources_allow_the_synthetic_root(self):
        root = "C:" + "/TaskCarry"
        for name in ("docs/en/windows-example.md", "docs/zh-CN/windows-example.md", "docs/zh-TW/windows-example.md",
                     "docs/en/manual-setup.md", "docs/zh-CN/manual-setup.md", "docs/zh-TW/manual-setup.md",
                     "examples/windows_quickstart/bootstrap.py"):
            for path in (root, root + "/runtime/Scripts/python.exe", root + "/control/"):
                with self.subTest(name=name, path=path):
                    self.assertTrue(reviewed_example_path(name, path))
                    screen_content({name: path.encode()})
        with self.assertRaises(RuntimeError):
            screen_content({"taskcarry/core.py": root.encode()})

    def test_other_roots_and_escapes_remain_rejected(self):
        root = "C:" + "/TaskCarry"
        for path in (root + "Other/file.md", root + "/../private.md",
                     root + "/./private.md", root + "/control/../../private.md",
                     "D:" + "/TaskCarry", "C:" + "/Users/example/private.md"):
            with self.subTest(path=path), self.assertRaises(RuntimeError):
                screen_content({"docs/en/windows-example.md": path.encode()})

    def test_complete_quoted_paths_and_standalone_lines_are_allowed(self):
        root = "C:" + "/TaskCarry"
        path = root + "/runtime/Scripts/python.exe"
        for text in ("Use `" + path + "` now.", "& '" + path + "' -m taskcarry",
                     'Run "' + path + '" next.', "  " + path + "  \r\n"):
            with self.subTest(text=text):
                screen_content({"docs/en/windows-example.md": text.encode()})

    def test_quoted_paths_are_checked_in_full_including_spaces_and_parentheses(self):
        root = "C:" + "/TaskCarry"
        for path in (root + "/with space/../../Users/example/private.md",
                     root + "/(scratch)/../../Users/example/private.md"):
            for quote in ('"', "'", "`"):
                with self.subTest(path=path, quote=quote), self.assertRaisesRegex(RuntimeError, "unreviewed_absolute_path"):
                    screen_content({"docs/en/windows-example.md": (quote + path + quote).encode()})

    def test_unquoted_paths_cannot_allow_a_truncated_prefix(self):
        root = "C:" + "/TaskCarry"
        for text in (root + "/with space/../../Users/example/private.md",
                     root + "/(scratch)/../../Users/example/private.md",
                     "Use " + root + "/control here.",
                     "Use " + root + "; this is an unquoted narrative path."):
            with self.subTest(text=text), self.assertRaisesRegex(RuntimeError, "unreviewed_absolute_path"):
                screen_content({"docs/en/windows-example.md": text.encode()})

    def test_secret_and_private_token_screens_still_apply_to_tutorial(self):
        root = "C:" + "/TaskCarry"
        with self.assertRaises(RuntimeError):
            screen_content({"docs/en/windows-example.md": (root + " PRIVATE_TOKEN").encode()},
                           ["PRIVATE_TOKEN"])
        with self.assertRaises(RuntimeError):
            screen_content({"docs/en/windows-example.md": (root + " sk-" + "a" * 40).encode()})

    def test_reviewed_image_cannot_be_replaced_or_allow_other_binary_assets(self):
        name = "docs/assets/workspace-sidebar-example.png"
        content = (Path(__file__).resolve().parents[1] / name).read_bytes()
        screen_content({name: content})
        with self.assertRaisesRegex(RuntimeError, "reviewed_asset_changed"):
            screen_content({name: content + b"unreviewed change"})
        with self.assertRaisesRegex(RuntimeError, "unexpected_binary"):
            screen_content({"docs/assets/unreviewed.png": content})


if __name__ == "__main__":
    unittest.main()
