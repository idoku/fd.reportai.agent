from __future__ import annotations

from dataclasses import replace
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRC = ROOT / "packages" / "fd-reportai-word" / "src"
INPUT_PATH = ROOT / "inputs" / "land_input.json"
OUTPUT_DIR = ROOT / "inputs" / "_outputs"

if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from fd_reportai_word import WordPipeline, get_default_ruleset  # noqa: E402
from fd_reportai_word.llm import LLMLocator  # noqa: E402
from fd_reportai_word.rules.land.computed_fields import LAND_COMPUTED_FIELDS  # noqa: E402


def load_land_elements() -> dict[str, object]:
    return json.loads(INPUT_PATH.read_text(encoding="utf-8"))


def run_land_pipeline(ruleset_name: str):
    framework = replace(
        get_default_ruleset(ruleset_name),
        computed_fields=list(LAND_COMPUTED_FIELDS),
    )
    api_key = os.getenv("DOUBAO_MODEL_KEY")
    model_name = os.getenv("DOUBAO_MODEL_NAME")
    base_url = os.getenv("DOUBAO_MODEL_URL") or "https://ark.cn-beijing.volces.com/api/v3"
    if not api_key:
        raise RuntimeError("DOUBAO_MODEL_KEY is not configured. Real LLM tests require Doubao credentials.")
    if not model_name:
        raise RuntimeError("DOUBAO_MODEL_NAME is not configured. Set it to your Doubao endpoint/model id.")
    pipeline = WordPipeline(
        locator=LLMLocator(
            provider="doubao",
            model=model_name,
            api_key=api_key,
            base_url=base_url,
        )
    )
    return pipeline.run(
        framework=framework,
        elements=load_land_elements(),
        metadata={"input_base_dir": str(ROOT / "inputs")},
    )


def render_ruleset_markdown(ruleset_name: str) -> str:
    return run_land_pipeline(ruleset_name).rendered_output["markdown"]


def write_output(name: str, content: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{name}.md"
    output_path.write_text(content.strip() + "\n", encoding="utf-8")
    return output_path
