from __future__ import annotations

import runpy
import tempfile
import unittest
from pathlib import Path


MODULE = runpy.run_path(
    str(Path(__file__).parents[1] / "scripts" / "refactor_okf_collections.py"),
    run_name="refactor_okf_collections_test",
)


class RefactorOkfCollectionsTests(unittest.TestCase):
    def test_structural_split_ignores_fenced_h2(self) -> None:
        body = "# Parent\n\n## First\n\n```md\n## Not a concept\n```\n\n## Second\nBody\n"
        preamble, sections = MODULE["split_h2"](body)
        self.assertEqual(preamble, "# Parent\n\n")
        self.assertEqual([section.title for section in sections], ["First", "Second"])
        self.assertIn("## Not a concept", sections[0].body)

    def test_raw_heading_mode_recovers_malformed_fences(self) -> None:
        body = "# Parent\n\n## First\n\n```md\ncontent\n## Recovered\nBody\n"
        _, sections = MODULE["split_h2"](body, raw_headings=True)
        self.assertEqual([section.title for section in sections], ["First", "Recovered"])

    def test_chronology_split_uses_dated_confidence_markers(self) -> None:
        body = (
            "# Journal\n\nIntroduction.\n\n"
            "First result, 2026-08-10. Confidence: high.\n\nDetails.\n\n"
            "Second result, 2026-08-11. Confidence: medium.\n\nMore details.\n"
        )
        preamble, sections, suffix = MODULE["split_chronology"](body, False)
        self.assertIn("Introduction", preamble)
        self.assertEqual(len(sections), 2)
        self.assertEqual(suffix, "")
        self.assertTrue(sections[0].title.startswith("First result"))

    def test_relative_links_are_relocated(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        old_parent = root / "wiki" / "pages"
        new_parent = old_parent / "collection"
        target = root / "docs" / "guide.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
        relocated = MODULE["relocate_links"](
            "See [guide](../../docs/guide.md).\n",
            old_parent,
            new_parent,
        )
        self.assertIn("../../../docs/guide.md", relocated)


if __name__ == "__main__":
    unittest.main()
