import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRef } from "react";
import { ChatTimeline } from "../components/chat/ChatTimeline";
import { ChatInput } from "../components/chat/ChatInput";
import * as pointerEnv from "../utils/pointerEnv";
import { shouldUseAppContextMenu } from "../utils/pointerEnv";
import * as clipboard from "../utils/clipboard";
import type { ChatMessage } from "../types";

const sampleMessages: ChatMessage[] = [
  {
    id: "m1",
    role: "user",
    content: "Ciao laboratorio",
    timestamp: "10:00",
  },
  {
    id: "m2",
    role: "assistant",
    content: "Pronto ad aiutare",
    timestamp: "10:01",
  },
];

describe("pointerEnv", () => {
  it("disables app context menu on Android UA", () => {
    const original = navigator.userAgent;
    Object.defineProperty(navigator, "userAgent", {
      configurable: true,
      value: "Mozilla/5.0 (Linux; Android 13) AppleWebKit Mobile",
    });
    expect(shouldUseAppContextMenu()).toBe(false);
    Object.defineProperty(navigator, "userAgent", {
      configurable: true,
      value: original,
    });
  });
});

describe("chat message copy UX (desktop)", () => {
  beforeEach(() => {
    vi.spyOn(pointerEnv, "shouldUseAppContextMenu").mockReturnValue(true);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("marks messages as selectable", () => {
    const ref = createRef<HTMLDivElement>();
    render(
      <ChatTimeline
        messages={sampleMessages}
        containerRef={ref}
        onScroll={() => {}}
        showNewMessages={false}
        onJumpToLatest={() => {}}
      />,
    );
    const msgs = [
      ...screen.getAllByTestId("message-user"),
      ...screen.getAllByTestId("message-assistant"),
    ];
    expect(msgs.length).toBeGreaterThan(0);
    msgs.forEach((el) => expect(el).toHaveAttribute("data-selectable", "true"));
    expect(screen.getAllByTestId("message-content")[0]).toHaveTextContent(
      "Ciao laboratorio",
    );
  });

  it("opens message context menu with Copia and Seleziona tutto", () => {
    const ref = createRef<HTMLDivElement>();
    render(
      <ChatTimeline
        messages={sampleMessages}
        containerRef={ref}
        onScroll={() => {}}
        showNewMessages={false}
        onJumpToLatest={() => {}}
      />,
    );
    const bubble = screen.getAllByTestId("message-user")[0];
    fireEvent.contextMenu(bubble, { clientX: 40, clientY: 60 });
    expect(screen.getByTestId("message-context-menu")).toBeInTheDocument();
    expect(screen.getByTestId("context-menu-copy")).toHaveTextContent("Copia");
    expect(screen.getByTestId("context-menu-select-all")).toHaveTextContent(
      "Seleziona tutto",
    );
  });

  it("disables Copia when nothing is selected", () => {
    const ref = createRef<HTMLDivElement>();
    render(
      <ChatTimeline
        messages={sampleMessages}
        containerRef={ref}
        onScroll={() => {}}
        showNewMessages={false}
        onJumpToLatest={() => {}}
      />,
    );
    fireEvent.contextMenu(screen.getAllByTestId("message-user")[0]);
    expect(screen.getByTestId("context-menu-copy")).toBeDisabled();
  });

  it("copies selected text via system clipboard helper", async () => {
    const writeSpy = vi
      .spyOn(clipboard, "writeClipboardText")
      .mockResolvedValue(true);
    vi.spyOn(clipboard, "getDomSelectionText").mockReturnValue("Ciao");
    const ref = createRef<HTMLDivElement>();
    render(
      <ChatTimeline
        messages={sampleMessages}
        containerRef={ref}
        onScroll={() => {}}
        showNewMessages={false}
        onJumpToLatest={() => {}}
      />,
    );
    fireEvent.contextMenu(screen.getAllByTestId("message-user")[0]);
    expect(screen.getByTestId("context-menu-copy")).not.toBeDisabled();
    fireEvent.click(screen.getByTestId("context-menu-copy"));
    await waitFor(() => {
      expect(writeSpy).toHaveBeenCalledWith("Ciao");
    });
  });

  it("does not open custom menu when mobile/native mode", () => {
    vi.spyOn(pointerEnv, "shouldUseAppContextMenu").mockReturnValue(false);
    const ref = createRef<HTMLDivElement>();
    render(
      <ChatTimeline
        messages={sampleMessages}
        containerRef={ref}
        onScroll={() => {}}
        showNewMessages={false}
        onJumpToLatest={() => {}}
      />,
    );
    fireEvent.contextMenu(screen.getAllByTestId("message-user")[0]);
    expect(screen.queryByTestId("message-context-menu")).not.toBeInTheDocument();
  });
});

describe("chat composer copy/paste UX (desktop)", () => {
  beforeEach(() => {
    vi.spyOn(pointerEnv, "shouldUseAppContextMenu").mockReturnValue(true);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("does not block Ctrl shortcuts on keydown (only Enter)", async () => {
    const onSend = vi.fn();
    render(
      <ChatInput onSend={onSend} onVoice={() => {}} coreState="IDLE" />,
    );
    const input = screen.getByTestId("chat-composer");
    await userEvent.type(input, "abc");
    fireEvent.keyDown(input, { key: "a", ctrlKey: true });
    fireEvent.keyDown(input, { key: "c", ctrlKey: true });
    fireEvent.keyDown(input, { key: "v", ctrlKey: true });
    fireEvent.keyDown(input, { key: "x", ctrlKey: true });
    expect(onSend).not.toHaveBeenCalled();
    expect(input).toHaveValue("abc");
  });

  it("Enter sends and Shift+Enter does not", async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();
    render(
      <ChatInput onSend={onSend} onVoice={() => {}} coreState="IDLE" />,
    );
    const input = screen.getByTestId("chat-composer");
    await user.type(input, "linea");
    fireEvent.keyDown(input, { key: "Enter", shiftKey: true });
    expect(onSend).not.toHaveBeenCalled();
    fireEvent.keyDown(input, { key: "Enter", shiftKey: false });
    expect(onSend).toHaveBeenCalledWith("linea");
  });

  it("opens composer context menu with cut/copy/paste/select-all", async () => {
    vi.spyOn(clipboard, "readClipboardText").mockResolvedValue("incolla");
    render(
      <ChatInput onSend={() => {}} onVoice={() => {}} coreState="IDLE" />,
    );
    const input = screen.getByTestId("chat-composer") as HTMLTextAreaElement;
    await userEvent.type(input, "hello");
    input.setSelectionRange(0, 5);
    fireEvent.contextMenu(input, { clientX: 10, clientY: 10 });
    expect(screen.getByTestId("composer-context-menu")).toBeInTheDocument();
    expect(screen.getByTestId("context-menu-cut")).toBeInTheDocument();
    expect(screen.getByTestId("context-menu-copy")).not.toBeDisabled();
    await waitFor(() => {
      expect(screen.getByTestId("context-menu-paste")).not.toBeDisabled();
    });
    expect(screen.getByTestId("context-menu-select-all")).toBeInTheDocument();
  });

  it("Copia writes selection to clipboard", async () => {
    const writeSpy = vi
      .spyOn(clipboard, "writeClipboardText")
      .mockResolvedValue(true);
    render(
      <ChatInput onSend={() => {}} onVoice={() => {}} coreState="IDLE" />,
    );
    const input = screen.getByTestId("chat-composer") as HTMLTextAreaElement;
    await userEvent.type(input, "copyme");
    input.setSelectionRange(0, 6);
    fireEvent.contextMenu(input);
    fireEvent.click(screen.getByTestId("context-menu-copy"));
    await waitFor(() => {
      expect(writeSpy).toHaveBeenCalledWith("copyme");
    });
  });

  it("Incolla inserts clipboard text", async () => {
    vi.spyOn(clipboard, "readClipboardText").mockResolvedValue("PASTE");
    render(
      <ChatInput onSend={() => {}} onVoice={() => {}} coreState="IDLE" />,
    );
    const input = screen.getByTestId("chat-composer") as HTMLTextAreaElement;
    fireEvent.contextMenu(input);
    await waitFor(() => {
      expect(screen.getByTestId("context-menu-paste")).not.toBeDisabled();
    });
    fireEvent.click(screen.getByTestId("context-menu-paste"));
    await waitFor(() => {
      expect(input).toHaveValue("PASTE");
    });
  });

  it("Taglia removes selection after clipboard write", async () => {
    vi.spyOn(clipboard, "writeClipboardText").mockResolvedValue(true);
    render(
      <ChatInput onSend={() => {}} onVoice={() => {}} coreState="IDLE" />,
    );
    const input = screen.getByTestId("chat-composer") as HTMLTextAreaElement;
    await userEvent.type(input, "ab");
    input.setSelectionRange(0, 2);
    fireEvent.contextMenu(input);
    fireEvent.click(screen.getByTestId("context-menu-cut"));
    await waitFor(() => {
      expect(input).toHaveValue("");
    });
  });

  it("Seleziona tutto selects composer contents", async () => {
    render(
      <ChatInput onSend={() => {}} onVoice={() => {}} coreState="IDLE" />,
    );
    const input = screen.getByTestId("chat-composer") as HTMLTextAreaElement;
    await userEvent.type(input, "xyz");
    fireEvent.contextMenu(input);
    fireEvent.click(screen.getByTestId("context-menu-select-all"));
    expect(input.selectionStart).toBe(0);
    expect(input.selectionEnd).toBe(3);
  });
});
