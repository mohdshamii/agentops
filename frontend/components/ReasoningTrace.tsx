"use client";

import { useState } from "react";
import { ReasoningStep, ToolCall } from "@/lib/types";
import { BrainIcon, ChevronDownIcon, ChevronRightIcon, ToolIcon } from "./Icons";
import styles from "@/styles/chat.module.css";

interface Props {
  trace?: ReasoningStep[];
  toolCalls?: ToolCall[];
}

export default function ReasoningTrace({ trace, toolCalls }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  if ((!trace || trace.length === 0) && (!toolCalls || toolCalls.length === 0)) {
    return null;
  }

  const stepCount = (trace?.length || 0) + (toolCalls?.length || 0);

  return (
    <div className={styles.reasoningContainer}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={styles.reasoningToggleBtn}
      >
        <span className={styles.reasoningIcon}>
          <BrainIcon size={14} />
        </span>
        <span className={styles.reasoningTitle}>
          Multi-Step Reasoning & Tools ({stepCount} {stepCount === 1 ? "step" : "steps"})
        </span>
        <span className={styles.reasoningArrow}>
          {isOpen ? <ChevronDownIcon size={14} /> : <ChevronRightIcon size={14} />}
        </span>
      </button>

      {isOpen && (
        <div className={styles.reasoningContent}>
          {trace && trace.map((step, idx) => (
            <div key={idx} className={styles.reasoningStepCard}>
              <div className={styles.stepHeader}>
                <span className={styles.stepBadge}>Step {step.step || idx + 1}</span>
                <span className={styles.stepType}>{step.type || "reasoning"}</span>
              </div>

              {step.thought && (
                <div className={styles.stepThought}>
                  <strong>Thought:</strong> {step.thought}
                </div>
              )}

              {step.action && (
                <div className={styles.stepAction}>
                  <span className={styles.actionPill}>Action: {step.action}</span>
                  {step.action_input && (
                    <pre className={styles.actionInputPre}>
                      {typeof step.action_input === "object"
                        ? JSON.stringify(step.action_input, null, 2)
                        : String(step.action_input)}
                    </pre>
                  )}
                </div>
              )}

              {step.observation && (
                <div className={styles.stepObservation}>
                  <strong>Observation:</strong>
                  <pre className={styles.obsPre}>{step.observation}</pre>
                </div>
              )}
            </div>
          ))}

          {toolCalls && toolCalls.length > 0 && (
            <div className={styles.toolCallsSummary}>
              <h4>Tool Invocations</h4>
              {toolCalls.map((tc, idx) => (
                <div key={idx} className={styles.toolCallItem}>
                  <span className={styles.toolNameBadge}>
                    <ToolIcon size={12} /> {tc.tool}
                  </span>
                  <span className={styles.toolParamSnippet}>
                    {JSON.stringify(tc.params || {})}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
