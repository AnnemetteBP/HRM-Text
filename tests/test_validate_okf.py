from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "validate_okf.py"
SPEC = importlib.util.spec_from_file_location("validate_okf", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validate_okf = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_okf)


class ValidateOkfTests(unittest.TestCase):
    def make_bundle(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        bundle = Path(temporary.name)
        (bundle / "index.md").write_text(
            '---\nokf_version: "0.2"\n---\n# Bundle\n\n* [Concept](concept.md)\n',
            encoding="utf-8",
        )
        (bundle / "concept.md").write_text(
            "---\ntype: Reference\ntitle: Concept\nstatus: stable\nconfidence: high\n---\n# Concept\n",
            encoding="utf-8",
        )
        return temporary, bundle

    def test_minimal_bundle_is_valid(self) -> None:
        temporary, bundle = self.make_bundle()
        self.addCleanup(temporary.cleanup)
        errors, warnings = validate_okf.validate(bundle)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_missing_type_fails(self) -> None:
        temporary, bundle = self.make_bundle()
        self.addCleanup(temporary.cleanup)
        (bundle / "concept.md").write_text("---\ntitle: Missing type\n---\n# Concept\n", encoding="utf-8")
        errors, _ = validate_okf.validate(bundle)
        self.assertTrue(any("non-empty type" in error for error in errors))

    def test_index_must_list_immediate_children(self) -> None:
        temporary, bundle = self.make_bundle()
        self.addCleanup(temporary.cleanup)
        (bundle / "index.md").write_text('---\nokf_version: "0.2"\n---\n# Bundle\n', encoding="utf-8")
        errors, _ = validate_okf.validate(bundle)
        self.assertTrue(any("missing immediate child link 'concept.md'" in error for error in errors))

    def test_subdirectory_requires_index(self) -> None:
        temporary, bundle = self.make_bundle()
        self.addCleanup(temporary.cleanup)
        child = bundle / "group"
        child.mkdir()
        (child / "item.md").write_text("---\ntype: Reference\n---\n# Item\n", encoding="utf-8")
        (bundle / "index.md").write_text(
            '---\nokf_version: "0.2"\n---\n# Bundle\n\n* [Concept](concept.md)\n* [Group](group/)\n',
            encoding="utf-8",
        )
        errors, _ = validate_okf.validate(bundle)
        self.assertTrue(any("directory requires index.md" in error for error in errors))

    def test_oversized_concept_fails(self) -> None:
        temporary, bundle = self.make_bundle()
        self.addCleanup(temporary.cleanup)
        concept = bundle / "concept.md"
        concept.write_text(
            "---\ntype: Reference\n---\n# Concept\n" + ("content\n" * 7_000),
            encoding="utf-8",
        )
        errors, _ = validate_okf.validate(bundle)
        self.assertTrue(any("split concepts at 50000 bytes" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
