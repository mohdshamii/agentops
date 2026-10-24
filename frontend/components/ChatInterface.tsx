"use client";

import { useState, useEffect, useRef } from "react";
import { apiClient } from "@/lib/api";
import { Message, Conversation, ReasoningStep, ToolCall } from "@/lib/types";
import { MODELS } from "@/lib/constants";
import Sidebar from "./Sidebar";
import MessageList from "./MessageList";
import PromptComposer from "./PromptComposer";
import AgentWorkspace from "./AgentWorkspace";
import Dashboard from "./Dashboard";
import WorkflowsView from "./WorkflowsView";
import DatabaseExplorer from "./DatabaseExplorer";
import { SidebarToggleIcon, WorkspaceIcon, CloseIcon } from "./Icons";
import styles from "@/styles/chat.module.css";

export default function ChatInterface() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedModel, setSelectedModel] = useState(MODELS[0].id);

  // Layout states
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [workspaceOpen, setWorkspaceOpen] = useState(true);
  const [activeView, setActiveView] = useState("chat");

  // Telemetry for Agent Workspace
  const [currentTrace, setCurrentTrace] = useState<ReasoningStep[]>([]);
  const [currentToolCalls, setCurrentToolCalls] = useState<ToolCall[]>([]);
  const [currentSources, setCurrentSources] = useState<Array<{ title: string; url: string; snippet?: string }>>([]);
  const [currentMemories, setCurrentMemories] = useState<string[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [activeConversation?.messages, loading]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadConversations = async () => {
    try {
      const list = await apiClient.getConversations();
      setConversations(list);
      if (list.length > 0 && !activeConversation) {
        setActiveConversation(list[0]);
        syncWorkspaceData(list[0]);
      } else if (list.length === 0) {
        handleNewConversation();
      }
    } catch (err: any) {
      console.error("Could not load conversations:", err);
      handleNewConversation();
    }
  };

  const syncWorkspaceData = (conv: Conversation) => {
    const asstMsgs = conv.messages.filter((m) => m.role === "assistant");
    if (asstMsgs.length > 0) {
      const latest = asstMsgs[asstMsgs.length - 1];
      if (latest.reasoning_trace) setCurrentTrace(latest.reasoning_trace);
      if (latest.tool_calls) setCurrentToolCalls(latest.tool_calls);
    }
  };

  const handleNewConversation = async () => {
    try {
      setError("");
      const newConv = await apiClient.createConversation();
      setConversations((prev) => [newConv, ...prev.filter((c) => c.id !== newConv.id)]);
      setActiveConversation(newConv);
      setCurrentTrace([]);
      setCurrentToolCalls([]);
      setCurrentSources([]);
      setCurrentMemories([]);
    } catch (err: any) {
      setError("Failed to create new conversation.");
    }
  };

  const handleSelectConversation = async (convId: string) => {
    try {
      setError("");
      const conv = await apiClient.getConversation(convId);
      setActiveConversation(conv);
      syncWorkspaceData(conv);
    } catch (err: any) {
      setError("Failed to load conversation details.");
    }
  };

  const handleDeleteConversation = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiClient.deleteConversation(convId);
      const remaining = conversations.filter((c) => c.id !== convId);
      setConversations(remaining);
      if (activeConversation?.id === convId) {
        if (remaining.length > 0) {
          setActiveConversation(remaining[0]);
          syncWorkspaceData(remaining[0]);
        } else {
          handleNewConversation();
        }
      }
    } catch (err: any) {
      setError("Failed to delete conversation.");
    }
  };

  const handleSendMessage = async (
    message: string,
    imageBase64?: string,
    options?: { enableSearch?: boolean; model?: string }
  ) => {
    if (!activeConversation) return;

    setLoading(true);
    setError("");

    const targetModel = options?.model || selectedModel;

    const tempUserMsg: Message = {
      id: `user-${Date.now()}`,
      conversation_id: activeConversation.id,
      role: "user",
      content: message,
      tokens_used: 0,
      created_at: new Date().toISOString(),
    };

    setActiveConversation((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        messages: [...prev.messages, tempUserMsg],
      };
    });

    setWorkspaceOpen(true);

    let accumulatedResponse = "";
    const tempAssistantId = `assistant-${Date.now()}`;

    apiClient.streamMessage(
      {
        message,
        conversation_id: activeConversation.id,
        model: targetModel,
        persona: "assistant",
        enable_reasoning: true,
        enable_tools: true,
      },
      {
        onInit: (data) => {
          setActiveConversation((prev) => {
            if (!prev) return null;
            return {
              ...prev,
              messages: [
                ...prev.messages,
                {
                  id: tempAssistantId,
                  conversation_id: data.conversation_id,
                  role: "assistant",
                  content: "",
                  tokens_used: 0,
                  created_at: new Date().toISOString(),
                },
              ],
            };
          });
        },
        onTrace: (trace) => {
          setCurrentTrace(trace);
          const extractedSources: any[] = [];
          trace.forEach((step: any) => {
            if (step.observation && step.observation.includes("http")) {
              const urlMatches = step.observation.match(/https?:\/\/[^\s"',]+/g);
              if (urlMatches) {
                urlMatches.slice(0, 3).forEach((u: string) => {
                  extractedSources.push({ title: "Web Intelligence", url: u });
                });
              }
            }
          });
          if (extractedSources.length > 0) setCurrentSources(extractedSources);

          setActiveConversation((prev) => {
            if (!prev) return null;
            const msgs = [...prev.messages];
            const lastIdx = msgs.findIndex((m) => m.id === tempAssistantId);
            if (lastIdx !== -1) {
              msgs[lastIdx].reasoning_trace = trace;
            }
            return { ...prev, messages: msgs };
          });
        },
        onToken: (token) => {
          accumulatedResponse += token;
          setActiveConversation((prev) => {
            if (!prev) return null;
            const msgs = [...prev.messages];
            const lastIdx = msgs.findIndex((m) => m.id === tempAssistantId);
            if (lastIdx !== -1) {
              msgs[lastIdx].content = accumulatedResponse;
            }
            return { ...prev, messages: msgs };
          });
        },
        onDone: (doneData) => {
          setLoading(false);
          loadConversations();
        },
        onError: (err) => {
          console.error("Streaming error, falling back to sync API:", err);
          apiClient
            .sendMessage({
              message,
              conversation_id: activeConversation.id,
              model: targetModel,
              persona: "assistant",
              enable_reasoning: true,
              enable_tools: true,
              image_base64: imageBase64,
            })
            .then((res) => {
              setActiveConversation((prev) => {
                if (!prev) return null;
                return {
                  ...prev,
                  messages: [
                    ...prev.messages.filter((m) => m.id !== tempAssistantId),
                    {
                      id: res.message_id,
                      conversation_id: res.conversation_id,
                      role: "assistant",
                      content: res.response,
                      reasoning_trace: res.reasoning_trace,
                      tool_calls: res.tool_calls,
                      tokens_used: res.tokens_used,
                      created_at: res.timestamp,
                    },
                  ],
                };
              });
              if (res.reasoning_trace) setCurrentTrace(res.reasoning_trace);
              if (res.tool_calls) setCurrentToolCalls(res.tool_calls);
            })
            .catch((e: any) => setError(e.message || "Request failed"))
            .finally(() => setLoading(false));
        },
      }
    );
  };

  const handlePromptSuggestion = (promptText: string) => {
    handleSendMessage(promptText);
  };

  const currentModelName = (MODELS.find((m) => m.id === selectedModel) || MODELS[0]).name;

  return (
    <div className={styles.appShell}>
      {/* Collapsible Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        conversations={conversations}
        activeConversationId={activeConversation?.id}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        isWorkspaceOpen={workspaceOpen}
        onToggleWorkspace={() => setWorkspaceOpen(!workspaceOpen)}
        activeView={activeView}
        onSelectView={setActiveView}
      />

      {/* Central Content Area */}
      <div className={styles.centerContainer}>
        {/* Top Header */}
        <header className={styles.topHeader}>
          <div className={styles.topHeaderLeft}>
            {!sidebarOpen && (
              <button
                type="button"
                onClick={() => setSidebarOpen(true)}
                className={styles.headerIconButton}
                title="Expand Sidebar"
              >
                <SidebarToggleIcon size={16} />
              </button>
            )}
            <div className={styles.headerModelPill}>
              <span className={styles.modelIndicatorDot}></span>
              <span className={styles.modelPillText}>{currentModelName}</span>
            </div>
          </div>

          <div className={styles.topHeaderRight}>
            <button
              type="button"
              onClick={() => setWorkspaceOpen(!workspaceOpen)}
              className={`${styles.workspaceToggleBtn} ${workspaceOpen ? styles.workspaceBtnActive : ""}`}
              title="Toggle Agent Workspace"
            >
              <WorkspaceIcon size={15} />
              <span>Workspace</span>
            </button>
          </div>
        </header>

        {/* Error Alert */}
        {error && (
          <div className={styles.errorAlert}>
            <span>{error}</span>
            <button onClick={() => setError("")} className={styles.closeAlertBtn}>
              <CloseIcon size={14} />
            </button>
          </div>
        )}

        {/* View Switcher Content */}
        {activeView === "chat" && (
          <>
            <div className={styles.scrollableFeed}>
              <MessageList
                messages={activeConversation?.messages || []}
                loading={loading}
                onOpenWorkspace={() => setWorkspaceOpen(true)}
                onPromptSuggestion={handlePromptSuggestion}
              />
              <div ref={messagesEndRef} />
            </div>

            <PromptComposer
              onSend={handleSendMessage}
              disabled={loading}
              activeModel={selectedModel}
              onSelectModel={setSelectedModel}
            />
          </>
        )}

        {activeView === "dashboard" && (
          <div className={styles.scrollableFeed}>
            <Dashboard />
          </div>
        )}

        {activeView === "workflows" && (
          <div className={styles.scrollableFeed}>
            <WorkflowsView />
          </div>
        )}

        {activeView === "database" && (
          <div className={styles.scrollableFeed}>
            <DatabaseExplorer />
          </div>
        )}
      </div>

      {/* Agent Workspace Side Panel */}
      <AgentWorkspace
        isOpen={workspaceOpen}
        onClose={() => setWorkspaceOpen(false)}
        reasoningTrace={currentTrace}
        toolCalls={currentToolCalls}
        sources={currentSources}
        memories={currentMemories}
        activeModel={selectedModel}
        isExecuting={loading}
      />
    </div>
  );
}