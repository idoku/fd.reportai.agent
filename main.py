from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PACKAGE_SRC = ROOT / "packages" / "fd-reportai-word" / "src"

if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from fd_reportai_word import LLMLocator, LandReportRunner  # noqa: E402
from fd_reportai_word.llm.config import env_float, env_str, load_dotenv_if_available  # noqa: E402


def main() -> None:
    load_dotenv_if_available(ROOT)

    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "inputs" / "land_input.json"
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "inputs" / "_outputs" / "land_report_cover.md"

    locator = LLMLocator(
        provider=env_str("FD_REPORTAI_LLM_PROVIDER", "doubao"),
        model=env_str("FD_REPORTAI_LLM_MODEL"),
        api_key=env_str("OPENAI_API_KEY"),
        base_url=env_str("OPENAI_BASE_URL"),
        temperature=env_float("TEMPERATURE", 0.3),
    )
    artifacts = LandReportRunner(locator=locator).run_from_file(
        input_path,
        output_path=output_path,
    )
    print(f"Markdown written to: {artifacts.output_path}")


if __name__ == "__main__":
    main()
