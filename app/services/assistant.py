"""Assistant use-cases. Callers never depend on a specific AI vendor."""

from ai.prompts import TECHNICAL_SYSTEM_PROMPT
from ai.router import AIRouter, RoutingHints
from ai.schemas import (
    GenerationRequest,
    GenerationResponse,
    ImageGenerationRequest,
    ImageReference,
)


class AssistantService:
    def __init__(self, router: AIRouter) -> None:
        self._router = router

    @property
    def router(self) -> AIRouter:
        return self._router

    def ask(self, question: str) -> GenerationResponse:
        request = GenerationRequest(
            prompt=question,
            system_prompt=TECHNICAL_SYSTEM_PROMPT,
        )
        return self._router.generate(request)

    def ask_with_images(
        self,
        question: str,
        images: list[ImageReference],
    ) -> GenerationResponse:
        request = ImageGenerationRequest(
            prompt=question,
            system_prompt=TECHNICAL_SYSTEM_PROMPT,
            images=images,
        )
        return self._router.generate_with_image(
            request, hints=RoutingHints(requires_image=True)
        )
