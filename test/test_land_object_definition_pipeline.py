from __future__ import annotations

import unittest

from land_pipeline_support import render_ruleset_markdown, write_output


class TestLandObjectDefinitionPipeline(unittest.TestCase):
    def test_render_object_definition_output(self) -> None:
        write_output(
            "land_object_definition",
            render_ruleset_markdown("ruleset_land_object_definition"),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
