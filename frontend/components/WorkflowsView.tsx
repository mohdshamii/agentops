"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import { WorkflowItem } from "@/lib/types";
import { BrainIcon, SpinnerIcon, CheckIcon } from "./Icons";
import styles from "@/styles/chat.module.css";

export default function WorkflowsView() {
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([]);
  const [activeWorkflow, setActiveWorkflow] = useState<WorkflowItem | null>(null);
  const [goal, setGoal] = useState("");
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      const data = await apiClient.getWorkflows();
      setWorkflows(data);
      if (data.length > 0 && !activeWorkflow) {
        setActiveWorkflow(data[0]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) return;

    setLoading(true);
    setError("");
    try {
      const created = await apiClient.createWorkflow(
        title.trim() || "Autonomous Goal Workflow",
        goal.trim()
      );
      setWorkflows((prev) => [created, ...prev]);
      setActiveWorkflow(created);
      setGoal("");
      setTitle("");
    } catch (err: any) {
      setError("Failed to create workflow plan.");
    } finally {
      setLoading(false);
    }
  };

  const handleRunWorkflow = async (id: string) => {
    setExecuting(true);
    setError("");
    try {
      const updated = await apiClient.runWorkflow(id);
      setActiveWorkflow(updated);
      loadWorkflows();
    } catch (err: any) {
      setError("Failed during workflow execution.");
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className={styles.workflowsContainer}>
      <div className={styles.workflowsSidebar}>
        <h3>Autonomous Workflows</h3>
        <p className={styles.subtext}>Goal decomposition and multi-step execution</p>

        <form onSubmit={handleCreateWorkflow} className={styles.newWorkflowForm}>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Workflow Title (e.g. Market Research)"
            className={styles.inputField}
          />
          <textarea
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="Describe your high-level goal in detail..."
            className={styles.textareaField}
            rows={3}
            required
          />
          <button type="submit" disabled={loading || !goal.trim()} className={styles.actionBtn}>
            {loading ? "Decomposing..." : "+ Generate Autonomous Plan"}
          </button>
        </form>

        <div className={styles.workflowList}>
          {workflows.map((wf) => (
            <div
              key={wf.id}
              onClick={() => setActiveWorkflow(wf)}
              className={`${styles.wfItem} ${activeWorkflow?.id === wf.id ? styles.wfItemActive : ""}`}
            >
              <div className={styles.wfItemHeader}>
                <strong>{wf.title}</strong>
                <span className={`${styles.statusPill} ${styles[wf.status]}`}>{wf.status}</span>
              </div>
              <p className={styles.wfGoalSnippet}>{wf.goal}</p>
            </div>
          ))}
        </div>
      </div>

      <div className={styles.workflowsDetailPanel}>
        {activeWorkflow ? (
          <div>
            <div className={styles.detailHeader}>
              <div>
                <h2>{activeWorkflow.title}</h2>
                <p className={styles.detailGoal}><strong>Goal:</strong> {activeWorkflow.goal}</p>
              </div>
              {activeWorkflow.status !== "completed" && (
                <button
                  onClick={() => handleRunWorkflow(activeWorkflow.id)}
                  disabled={executing}
                  className={styles.runWfBtn}
                >
                  {executing ? (
                    <span style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
                      <SpinnerIcon size={14} /> Executing Steps Autonomously...
                    </span>
                  ) : (
                    "Run Autonomous Workflow"
                  )}
                </button>
              )}
            </div>

            {error && <div className={styles.error}>{error}</div>}

            {/* Steps & Results */}
            <div className={styles.stepsSection}>
              <h3>Planned Execution Steps ({activeWorkflow.plan.length})</h3>
              <div className={styles.stepsList}>
                {activeWorkflow.plan.map((step) => {
                  const resultMatch = activeWorkflow.results?.find((r) => r.step === step.step);
                  return (
                    <div key={step.step} className={styles.workflowStepCard}>
                      <div className={styles.stepCardHeader}>
                        <span className={styles.stepNumberBadge}>Step {step.step}</span>
                        {step.recommended_tool && (
                          <span className={styles.toolPill}>Tool: {step.recommended_tool}</span>
                        )}
                        <span className={resultMatch ? styles.completedPill : styles.pendingPill}>
                          {resultMatch ? (
                            <span style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem" }}>
                              <CheckIcon size={12} /> Completed
                            </span>
                          ) : (
                            "Pending"
                          )}
                        </span>
                      </div>
                      <p className={styles.stepDescText}>{step.description}</p>

                      {resultMatch && (
                        <div className={styles.stepResultBox}>
                          <strong>Output:</strong>
                          <pre className={styles.resultPre}>{resultMatch.output}</pre>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Final Synthesis Output */}
            {activeWorkflow.final_output && (
              <div className={styles.finalOutputSection}>
                <h3>Executive Synthesis & Final Deliverable</h3>
                <div className={styles.synthesisBox}>
                  <pre className={styles.synthesisPre}>{activeWorkflow.final_output}</pre>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className={styles.emptyDetail}>
            Select or create an autonomous workflow from the left sidebar to begin.
          </div>
        )}
      </div>
    </div>
  );
}
