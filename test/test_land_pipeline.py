from __future__ import annotations

import unittest

from land_pipeline_support import render_ruleset_markdown, write_output


class TestLandPipeline(unittest.TestCase):
    def test_render_full_land_report_output(self) -> None:
        write_output("land_report", render_ruleset_markdown("ruleset_land"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
