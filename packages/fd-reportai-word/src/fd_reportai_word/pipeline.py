from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .blocker import BaseBlocker, NoopBlocker
from .composer import BaseComposer, NoopComposer
from .config import ElementMap, ElementValue, WordPipelineConfig
from .context import WordContext
from .converters import BaseConverter, NoopConverter
from .detectors import BaseDetector, NoopDetector
from .planner import BasePlanner, NoopPlanner
from .renderer import BaseRenderer, NoopRenderer
from .rules.default_rulesets import apply_default_ruleset
from .validator import BaseValidator, NoopValidator


@dataclass(slots=True)
class WordPipeline:
    detectors: list[BaseDetector] = field(default_factory=lambda: [NoopDetector()])
    converters: list[BaseConverter] = field(default_factory=lambda: [NoopConverter()])
    planner: BasePlanner = field(default_factory=NoopPlanner)
    blocker: BaseBlocker = field(default_factory=NoopBlocker)
    composer: BaseComposer = field(default_factory=NoopComposer)
    validators: list[BaseValidator] = field(default_factory=lambda: [NoopValidator()])
    renderers: list[BaseRenderer] = field(default_factory=lambda: [NoopRenderer()])

    def create_context(
        self,
        framework: WordPipelineConfig,
        elements: dict[str, Any] | ElementMap | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WordContext:
        return WordContext(
            framework=framework,
            elements=self._normalize_elements(elements),
            metadata=metadata or {},
        )

    def run(
        self,
        context: WordContext | None = None,
        *,
        framework: WordPipelineConfig | None = None,
        elements: dict[str, Any] | ElementMap | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WordContext:
        if context is None:
            if framework is None:
                framework = apply_default_ruleset(WordContext()).framework
            context = self.create_context(
                framework=framework,
                elements=elements,
                metadata=metadata,
            )
        else:
            apply_default_ruleset(context)

        for detector in self.detectors:
            detector.detect(context)

        for converter in self.converters:
            converter.convert(context)

        self.planner.plan(context)
        self.blocker.block(context)
        self.composer.compose(context)

        for validator in self.validators:
            validator.validate(context)

        for renderer in self.renderers:
            renderer.render(context)

        if isinstance(context.rendered_output, dict):
            context.section_outputs = list(context.rendered_output.get("sections", []))

        return context

    def _normalize_elements(
        self,
        elements: dict[str, Any] | ElementMap | None,
    ) -> ElementMap:
        normalized: ElementMap = {}
        for key, value in (elements or {}).items():
            if isinstance(value, ElementValue):
                normalized[key] = value
            else:
                normalized[key] = ElementValue(value=value)
        return normalized
