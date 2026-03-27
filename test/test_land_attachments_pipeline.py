from __future__ import annotations

import unittest

from land_pipeline_support import render_ruleset_markdown, write_output


class TestLandAttachmentsPipeline(unittest.TestCase):
    def test_render_attachments_output(self) -> None:
        write_output("land_attachments", render_ruleset_markdown("ruleset_land_attachments"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
