"use client";

import { Message } from "@/lib/types";
import { formatDistanceToNow } from "date-fns";
import ReactMarkdown from "react-markdown";
import CodeBlock from "./CodeBlock";
import {
  LogoIcon,
  BrainIcon,
  GlobeIcon,
  DatabaseIcon,
  TerminalIcon,
  ExternalLinkIcon,
  SpinnerIcon
} from "./Icons";
import styles from "@/styles/chat.module.css";

interface Props {
  messages: Message[];
  loading: boolean;
  onOpenWorkspace: () => void;
  onPromptSuggestion: (text: string) => void;
}

export default function MessageList({
  messages,
  loading,
  onOpenWorkspace,
  onPromptSuggestion
}: Props) {
  return (
    <div className={styles.messageList}>
      {messages.length === 0 ? (
        <div className={styles.emptyState}>
          <div className={styles.emptyLogoCircle}>
            <LogoIcon size={34} />
          </div>
          <h2 className={styles.emptyTitle}>How can I help you today?</h2>
          <p className={styles.emptySubtitle}>
            AgentOps reasoning engine with live web intelligence, database execution, and autonomous workflows.
          </p>

          <div className={styles.suggestionsGrid}>
            <button
              onClick={() =>
                onPromptSuggestion(
                  "Search the web for recent advancements in open-source AI models and summarize top developments."
                )
              }
              className={styles.suggestionCard}
            >
              <div className={styles.suggestionHeader}>
                <GlobeIcon size={14} className={styles.suggestionIcon} />
                <span>Web Intelligence</span>
              </div>
              <p>Search and synthesize recent open-source AI developments.</p>
            </button>

            <button
              onClick={() =>
                onPromptSuggestion("Inspect the database schema and show all active conversation tables.")
              }
              className={styles.suggestionCard}
            >
              <div className={styles.suggestionHeader}>
                <DatabaseIcon size={14} className={styles.suggestionIcon} />
                <span>Database Query</span>
              </div>
              <p>Inspect SQLite schemas and verify table structures.</p>
            </button>

            <button
              onClick={() =>
                onPromptSuggestion(
                  "Write a clean Python function to calculate Fibonacci sequences and run benchmark tests."
                )
              }
              className={styles.suggestionCard}
            >
              <div className={styles.suggestionHeader}>
                <TerminalIcon size={14} className={styles.suggestionIcon} />
                <span>Code Sandbox</span>
              </div>
              <p>Execute Python scripts and verify algorithmic logic.</p>
            </button>

            <button
              onClick={() =>
                onPromptSuggestion("Initiate an autonomous goal workflow to analyze market metrics.")
              }
              className={styles.suggestionCard}
            >
              <div className={styles.suggestionHeader}>
                <BrainIcon size={14} className={styles.suggestionIcon} />
                <span>Autonomous Workflow</span>
              </div>
              <p>Launch an end-to-end multi-step plan with self-reflection.</p>
            </button>
          </div>
        </div>
      ) : (
        messages.map((msg, idx) => (
          <div key={msg.id || idx} className={`${styles.messageRow} ${styles[msg.role]}`}>
            {msg.role === "assistant" && (
              <div className={styles.assistantAvatar}>
                <LogoIcon size={16} />
              </div>
            )}

            <div className={styles.messageContentWrapper}>
              {/* Reasoning Trace Link Chip */}
              {msg.role === "assistant" && msg.reasoning_trace && msg.reasoning_trace.length > 0 && (
                <button
                  type="button"
                  onClick={onOpenWorkspace}
                  className={styles.reasoningTriggerBadge}
                >
                  <BrainIcon size={13} />
                  <span>
                    Reasoning & Tool Execution ({msg.reasoning_trace.length} stages)
                  </span>
                </button>
              )}

              {/* Message Bubble */}
              <div className={styles.messageBubble}>
                <ReactMarkdown components={{ code: CodeBlock as any }}>
                  {msg.content}
                </ReactMarkdown>
              </div>

              {/* Tool Execution Pills */}
              {msg.role === "assistant" && msg.tool_calls && msg.tool_calls.length > 0 && (
                <div className={styles.toolsExecutedPills}>
                  {msg.tool_calls.map((tc, tIdx) => (
                    <button
                      key={tIdx}
                      type="button"
                      onClick={onOpenWorkspace}
                      className={styles.toolPillChip}
                    >
                      <TerminalIcon size={11} />
                      <span>{tc.tool}</span>
                    </button>
                  ))}
                </div>
              )}

              {/* Footer Timestamp */}
              <div className={styles.messageMetaFooter}>
                <span className={styles.timestamp}>
                  {msg.created_at
                    ? formatDistanceToNow(new Date(msg.created_at), { addSuffix: true })
                    : "Just now"}
                </span>
                {msg.tokens_used > 0 && (
                  <span className={styles.tokenCount}>
                    {msg.tokens_used} tokens
                  </span>
                )}
              </div>
            </div>
          </div>
        ))
      )}

      {/* Loading Indicator */}
      {loading && (
        <div className={`${styles.messageRow} ${styles.assistant}`}>
          <div className={styles.assistantAvatar}>
            <LogoIcon size={16} />
          </div>
          <div className={styles.messageContentWrapper}>
            <div className={styles.loadingBubble}>
              <SpinnerIcon size={15} />
              <span className={styles.loadingText}>
                Evaluating task plan and executing tools...
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}