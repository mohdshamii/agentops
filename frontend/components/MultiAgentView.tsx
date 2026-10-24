"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import { AgentRole } from "@/lib/types";
import {
  LogoIcon,
  GlobeIcon,
  TerminalIcon,
  DatabaseIcon,
  SearchIcon,
  CheckIcon,
  SpinnerIcon,
  ToolIcon
} from "./Icons";
import styles from "@/styles/chat.module.css";

export default function MultiAgentView() {
  const [agents, setAgents] = useState<AgentRole[]>([]);
  const [task, setTask] = useState("");
  const [running, setRunning] = useState(false);
  const [teamResult, setTeamResult] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      const data = await apiClient.getAgentsTeam();
      setAgents(data.agents || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleRunTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!task.trim()) return;

    setRunning(true);
    setError("");
    setTeamResult(null);

    try {
      const result = await apiClient.runMultiAgentTask(task);
      setTeamResult(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Multi-agent task failed.");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className={styles.multiAgentContainer}>
      <div className={styles.multiAgentHeader}>
        <h2>Multi-Agent Collaborative Swarm</h2>
        <p>
          Specialized autonomous agents collaborating to solve complex, multi-domain tasks.
        </p>
      </div>

      {/* Swarm Cards */}
      <div className={styles.swarmCardsGrid}>
        {agents.map((ag) => (
          <div key={ag.id} className={styles.agentCard}>
            <div className={styles.agentAvatar}>
              {ag.id === "supervisor" && <LogoIcon size={22} />}
              {ag.id === "researcher" && <GlobeIcon size={22} />}
              {ag.id === "coder" && <TerminalIcon size={22} />}
              {ag.id === "data_analyst" && <DatabaseIcon size={22} />}
              {ag.id === "reviewer" && <SearchIcon size={22} />}
            </div>
            <h4>{ag.name}</h4>
            <span className={styles.agentRoleLabel}>{ag.role}</span>
            <div className={styles.agentToolsPills}>
              {ag.allowed_tools.map((t) => (
                <span key={t} className={styles.agentToolBadge}>
                  <ToolIcon size={11} /> {t}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Task Launcher Form */}
      <div className={styles.taskLauncherBox}>
        <h3>Assign Mission to the Agent Swarm</h3>
        <form onSubmit={handleRunTask}>
          <textarea
            value={task}
            onChange={(e) => setTask(e.target.value)}
            placeholder="E.g. Analyze recent trends in open-source AI, write a python script to fetch model metrics from an API, query our database for active conversations, and produce a unified report."
            className={styles.taskTextarea}
            rows={3}
            required
          />
          <button type="submit" disabled={running || !task.trim()} className={styles.launchSwarmBtn}>
            {running ? (
              <span style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
                <SpinnerIcon size={14} /> Swarm Collaborating & Debating...
              </span>
            ) : (
              "Launch Multi-Agent Mission"
            )}
          </button>
        </form>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {/* Team Output Visualization */}
      {teamResult && (
        <div className={styles.teamResultSection}>
          <h3>Swarm Collaboration Report</h3>
          
          <div className={styles.agentStepsTimeline}>
            {teamResult.agent_team_steps?.map((step: any, idx: number) => (
              <div key={idx} className={styles.agentStepBox}>
                <div className={styles.agentStepHeader}>
                  <strong>{step.agent} ({step.role})</strong>
                  <span className={styles.completedPill}>
                    <CheckIcon size={12} /> Executed
                  </span>
                </div>
                <div className={styles.agentStepContent}>
                  <pre className={styles.agentOutputPre}>{step.output}</pre>
                </div>
              </div>
            ))}
          </div>

          <div className={styles.finalReviewerSynthesis}>
            <h3>Final Synthesized Deliverable</h3>
            <div className={styles.synthesisBox}>
              <pre className={styles.synthesisPre}>{teamResult.final_synthesis}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
