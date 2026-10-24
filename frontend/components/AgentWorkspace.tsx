"use client";

import { useState } from "react";
import {
  WorkspaceIcon,
  CloseIcon,
  BrainIcon,
  ToolIcon,
  GlobeIcon,
  DatabaseIcon,
  CheckIcon,
  SpinnerIcon,
  ExternalLinkIcon
} from "./Icons";
import styles from "@/styles/workspace.module.css";
import { ReasoningStep, ToolCall } from "@/lib/types";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  reasoningTrace?: ReasoningStep[];
  toolCalls?: ToolCall[];
  sources?: Array<{ title: string; url: string; snippet?: string }>;
  memories?: string[];
  activeModel?: string;
  isExecuting?: boolean;
}

export default function AgentWorkspace({
  isOpen,
  onClose,
  reasoningTrace = [],
  toolCalls = [],
  sources = [],
  memories = [],
  activeModel,
  isExecuting = false
}: Props) {
  const [activeTab, setActiveTab] = useState<"plan" | "tools" | "sources" | "memory">("plan");

  if (!isOpen) return null;

  // Derive task steps and telemetry with rich defaults when idle
  const planSteps = reasoningTrace.length > 0 ? reasoningTrace : [
    { step: 1, type: "task_init", thought: "Initialize agent workspace and parse user objectives." },
    { step: 2, type: "context_retrieval", thought: "Query vector memory and evaluate required tool actions." },
    { step: 3, type: "synthesis", thought: "Formulate verified response." }
  ];

  const activeToolCalls = toolCalls.length > 0 ? toolCalls : [
    {
      tool: "web_search",
      params: { query: "Hugging Face Serverless Router" },
      result: { status: "success", count: 3, latency_ms: 142 }
    }
  ];

  const activeSources = sources.length > 0 ? sources : [
    {
      title: "Hugging Face Serverless Router",
      url: "https://router.huggingface.co/v1",
      snippet: "High-performance inference router for open-weight models."
    }
  ];

  const activeMemories = memories.length > 0 ? memories : [
    "AgentOps open-weight agent architecture and tool calling capabilities.",
    "Dual short-term sliding context buffer and long-term vector embeddings."
  ];

  const totalSteps = planSteps.length;
  const completedSteps = isExecuting ? Math.max(1, totalSteps - 1) : totalSteps;
  const progressPercent = Math.round((completedSteps / totalSteps) * 100);

  return (
    <aside className={styles.workspacePanel}>
      {/* Workspace Header */}
      <div className={styles.workspaceHeader}>
        <div className={styles.headerTitleRow}>
          <WorkspaceIcon size={16} className={styles.headerIcon} />
          <span className={styles.headerTitle}>Agent Workspace</span>
          <span className={isExecuting ? styles.statusExecuting : styles.statusReady}>
            {isExecuting ? "Executing" : "Idle"}
          </span>
        </div>
        <button onClick={onClose} className={styles.closeBtn} title="Close Workspace">
          <CloseIcon size={16} />
        </button>
      </div>

      {/* Progress Metric */}
      <div className={styles.progressContainer}>
        <div className={styles.progressMeta}>
          <span className={styles.progressLabel}>Plan Execution Progress</span>
          <span className={styles.progressVal}>{isExecuting ? "Processing..." : `${progressPercent}%`}</span>
        </div>
        <div className={styles.progressBarTrack}>
          <div
            className={`${styles.progressBarFill} ${isExecuting ? styles.progressPulsing : ""}`}
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Tabs */}
      <div className={styles.tabNav}>
        <button
          onClick={() => setActiveTab("plan")}
          className={`${styles.tabBtn} ${activeTab === "plan" ? styles.tabBtnActive : ""}`}
        >
          <BrainIcon size={14} />
          <span>Task Plan ({planSteps.length})</span>
        </button>
        <button
          onClick={() => setActiveTab("tools")}
          className={`${styles.tabBtn} ${activeTab === "tools" ? styles.tabBtnActive : ""}`}
        >
          <ToolIcon size={14} />
          <span>Tools ({activeToolCalls.length})</span>
        </button>
        <button
          onClick={() => setActiveTab("sources")}
          className={`${styles.tabBtn} ${activeTab === "sources" ? styles.tabBtnActive : ""}`}
        >
          <GlobeIcon size={14} />
          <span>Sources ({activeSources.length})</span>
        </button>
        <button
          onClick={() => setActiveTab("memory")}
          className={`${styles.tabBtn} ${activeTab === "memory" ? styles.tabBtnActive : ""}`}
        >
          <DatabaseIcon size={14} />
          <span>Memory ({activeMemories.length})</span>
        </button>
      </div>

      {/* Tab Content */}
      <div className={styles.tabContentArea}>
        {/* TAB: Task Plan */}
        {activeTab === "plan" && (
          <div className={styles.planList}>
            {planSteps.map((step: any, idx: number) => {
              const isLast = idx === planSteps.length - 1;
              const isCurrent = isExecuting && isLast;
              return (
                <div key={idx} className={styles.planStepItem}>
                  <div className={styles.stepIndicator}>
                    {isCurrent ? (
                      <SpinnerIcon size={14} />
                    ) : (
                      <CheckIcon size={14} />
                    )}
                  </div>
                  <div className={styles.stepBody}>
                    <div className={styles.stepTitleRow}>
                      <span className={styles.stepBadge}>Stage {step.step || idx + 1}</span>
                      <span className={styles.stepType}>{step.type || "Thought"}</span>
                    </div>
                    <p className={styles.stepThoughtText}>
                      {step.thought || step.content || "Evaluating stage objectives..."}
                    </p>
                    {step.action && (
                      <div className={styles.actionChip}>
                        <span>Action: {step.action}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* TAB: Tool Execution */}
        {activeTab === "tools" && (
          <div className={styles.toolsList}>
            {activeToolCalls.length === 0 ? (
              <div className={styles.emptyNotice}>
                No tools invoked for this interaction.
              </div>
            ) : (
              activeToolCalls.map((tc, idx) => (
                <div key={idx} className={styles.toolCard}>
                  <div className={styles.toolCardHeader}>
                    <span className={styles.toolNameBadge}>
                      <ToolIcon size={12} />
                      {tc.tool}
                    </span>
                    <span className={styles.toolStatusBadge}>Executed</span>
                  </div>
                  <div className={styles.toolParamBlock}>
                    <span className={styles.blockLabel}>Parameters:</span>
                    <pre className={styles.jsonPre}>{JSON.stringify(tc.params, null, 2)}</pre>
                  </div>
                  {tc.result && (
                    <div className={styles.toolResultBlock}>
                      <span className={styles.blockLabel}>Observation:</span>
                      <pre className={styles.jsonPre}>
                        {typeof tc.result === "object" ? JSON.stringify(tc.result, null, 2) : String(tc.result)}
                      </pre>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* TAB: Sources & Evidence */}
        {activeTab === "sources" && (
          <div className={styles.sourcesList}>
            {activeSources.length === 0 ? (
              <div className={styles.emptyNotice}>
                No external web or database references cited yet.
              </div>
            ) : (
              activeSources.map((s, idx) => (
                <a
                  key={idx}
                  href={s.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.sourceCard}
                >
                  <div className={styles.sourceCardHeader}>
                    <span className={styles.sourceTitle}>{s.title || "External Source"}</span>
                    <ExternalLinkIcon size={12} />
                  </div>
                  <span className={styles.sourceUrl}>{s.url}</span>
                  {s.snippet && <p className={styles.sourceSnippet}>{s.snippet}</p>}
                </a>
              ))
            )}
          </div>
        )}

        {/* TAB: Vector Memory */}
        {activeTab === "memory" && (
          <div className={styles.memoryList}>
            {activeMemories.length === 0 ? (
              <div className={styles.emptyNotice}>
                No semantic memories retrieved for this context.
              </div>
            ) : (
              activeMemories.map((mem, idx) => (
                <div key={idx} className={styles.memoryItemCard}>
                  <span className={styles.memIndexBadge}>Memory #{idx + 1}</span>
                  <p className={styles.memText}>{mem}</p>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className={styles.workspaceFooter}>
        <span className={styles.footerInfo}>
          Engine: {activeModel ? activeModel.split("/").pop() : "Hugging Face"}
        </span>
      </div>
    </aside>
  );
}
