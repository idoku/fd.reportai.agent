from __future__ import annotations

import unittest

from land_pipeline_support import render_ruleset_markdown, write_output


class TestLandResultUsagePipeline(unittest.TestCase):
    def test_render_result_usage_output(self) -> None:
        write_output("land_result_usage", render_ruleset_markdown("ruleset_land_result_usage"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
