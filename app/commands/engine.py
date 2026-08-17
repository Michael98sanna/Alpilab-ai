"""Command resolution and mock execution."""

from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.commands import Action, ActionResult, Command, Intent
from app.schemas.enums import ActionRiskLevel, IntentType
from app.security.authorization import authorize_command
from app.tools.registry import ToolRegistry
from hub.mock_hub import MockAlpilabHub


class CommandEngine:
    """
    Separates commands/actions from free conversation.

    Does not execute dangerous operations; mock Hub calls only return placeholders.
    """

    def __init__(
        self,
        tool_registry: ToolRegistry | None = None,
        hub: MockAlpilabHub | None = None,
    ) -> None:
        self._tools = tool_registry or ToolRegistry()
        self._hub = hub or MockAlpilabHub()

    def build_command(self, repair_session_id: str, intent: Intent) -> Command:
        risk = ActionRiskLevel.SAFE
        if intent.type in {IntentType.OPEN_TOOL, IntentType.CAPTURE_IMAGE}:
            risk = ActionRiskLevel.CONFIRM_REQUIRED
        if intent.type == IntentType.RESET_DIAGNOSTIC_FLOW:
            risk = ActionRiskLevel.DANGEROUS

        command = Command(
            id=str(uuid4()),
            repair_session_id=repair_session_id,
            intent=intent,
            risk_level=risk,
            requires_confirmation=risk != ActionRiskLevel.READ_ONLY,
            created_at=datetime.now(timezone.utc),
        )
        auth = authorize_command(command)
        command.requires_confirmation = auth.requires_confirmation
        return command

    def resolve_action(self, command: Command) -> Action:
        intent = command.intent
        action_type = intent.type.value
        return Action(
            id=str(uuid4()),
            command_id=command.id,
            action_type=action_type,
            target=intent.target,
            parameters=dict(intent.parameters),
            risk_level=command.risk_level,
        )

    def execute_mock(self, action: Action) -> ActionResult:
        """Mock execution path — no real hardware or shell commands."""
        if action.action_type == IntentType.OPEN_TOOL.value and action.target:
            tool = self._tools.get(action.target)
            hub_result = self._hub.open_application(action.target)
            return ActionResult(
                action_id=action.id,
                success=hub_result.success,
                message=hub_result.message,
                data={"tool": tool.id if tool else action.target, "mock": True},
                executed_at=datetime.now(timezone.utc),
            )

        if action.action_type == IntentType.STOP.value:
            return ActionResult(
                action_id=action.id,
                success=True,
                message="[MOCK] Flusso guidato sospeso",
                data={"flow": "paused"},
                executed_at=datetime.now(timezone.utc),
            )

        if action.action_type == IntentType.CONTINUE_DIAGNOSIS.value:
            return ActionResult(
                action_id=action.id,
                success=True,
                message="[MOCK] Diagnosi ripresa dal contesto esistente",
                data={"flow": "resumed"},
                executed_at=datetime.now(timezone.utc),
            )

        return ActionResult(
            action_id=action.id,
            success=True,
            message="[MOCK] Action recorded",
            data={"action_type": action.action_type},
            executed_at=datetime.now(timezone.utc),
        )
