from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PACKAGE_SRC = ROOT / "packages" / "fd-reportai-word" / "src"

if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from fd_reportai_word import LLMLocator, WordContext, WordPipeline, get_default_ruleset  # noqa: E402
from fd_reportai_word.llm.config import env_float, env_str, load_dotenv_if_available  # noqa: E402


def _load_payload(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_context(payload: dict[str, object], ruleset_name: str) -> WordContext:
    if "elements" in payload or "detections" in payload or "metadata" in payload:
        return WordContext(
            framework=get_default_ruleset(ruleset_name),
            elements=payload.get("elements", {}),
            detections=payload.get("detections", []),
            metadata=payload.get("metadata", {}),
        )
    return WordContext(
        framework=get_default_ruleset(ruleset_name),
        elements=payload,
    )


def main() -> None:
    load_dotenv_if_available(ROOT)

    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "inputs" / "land_summary_input.json"
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "inputs" / "_outputs" / "report.md"
    ruleset_name = sys.argv[3] if len(sys.argv) > 3 else "ruleset_land"

    payload = _load_payload(input_path)
    context = _build_context(payload, ruleset_name)
    locator = LLMLocator(
        provider=env_str("FD_REPORTAI_LLM_PROVIDER", "mock"),
        model=env_str("FD_REPORTAI_LLM_MODEL"),
        api_key=env_str("OPENAI_API_KEY"),
        base_url=env_str("OPENAI_BASE_URL"),
        temperature=env_float("TEMPERATURE", 0.3),
    )
    result = WordPipeline(locator=locator).run(context=context)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.rendered_output["markdown"], encoding="utf-8")
    print(f"Markdown written to: {output_path}")


if __name__ == "__main__":
    main()
