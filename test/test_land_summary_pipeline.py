from __future__ import annotations

import unittest

from land_pipeline_support import render_ruleset_markdown, write_output


class TestLandSummaryPipeline(unittest.TestCase):
    def test_render_summary_output(self) -> None:
        write_output("land_summary", render_ruleset_markdown("ruleset_land_summary"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
