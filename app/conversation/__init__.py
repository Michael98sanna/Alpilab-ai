"""Conversation and command engine."""

__all__ = ["ConversationCommandEngine"]


def __getattr__(name: str):
    if name == "ConversationCommandEngine":
        from app.conversation.engine import ConversationCommandEngine as cls

        return cls
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
