"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import {
  LogoIcon,
  ToolIcon,
  BrainIcon,
  DatabaseIcon,
  TerminalIcon,
  CheckIcon
} from "./Icons";
import styles from "@/styles/chat.module.css";

export default function Dashboard() {
  const [stats, setStats] = useState({
    conversationsCount: 0,
    toolsCount: 0,
    memoriesCount: 0,
    workflowsCount: 0,
    health: "Checking...",
    defaultModel: "meta-llama/Llama-3.2-3B-Instruct"
  });
  const [toolLogs, setToolLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [healthData, convs, tools, memories, workflows, logs] = await Promise.all([
        apiClient.healthCheck().catch(() => ({ status: "online", models: {} })),
        apiClient.getConversations().catch(() => []),
        apiClient.getTools().catch(() => []),
        apiClient.getMemories().catch(() => []),
        apiClient.getWorkflows().catch(() => []),
        apiClient.getToolLogs().catch(() => [])
      ]);

      setStats({
        conversationsCount: convs.length,
        toolsCount: tools.length,
        memoriesCount: memories.length,
        workflowsCount: workflows.length,
        health: healthData.status || "healthy",
        defaultModel: healthData.models?.default || "meta-llama/Llama-3.2-3B-Instruct"
      });
      setToolLogs(logs);
    } catch (e) {
      console.error("Dashboard data load error:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.dashboardContainer}>
      <div className={styles.dashHeaderRow}>
        <div>
          <h2>Operations Dashboard</h2>
          <p className={styles.dashSubtitle}>
            Real-time telemetry, model status, and tool execution logs for AgentOps.
          </p>
        </div>
        <button onClick={loadDashboardData} className={styles.refreshBtn}>
          Refresh Telemetry
        </button>
      </div>

      {/* Metrics Grid */}
      <div className={styles.metricsGrid}>
        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>
            <LogoIcon size={20} />
          </div>
          <div className={styles.metricVal}>{stats.defaultModel.split("/").pop()}</div>
          <div className={styles.metricLabel}>Active Engine Model</div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>
            <BrainIcon size={20} />
          </div>
          <div className={styles.metricVal}>{stats.conversationsCount}</div>
          <div className={styles.metricLabel}>Total Conversations</div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>
            <ToolIcon size={20} />
          </div>
          <div className={styles.metricVal}>{stats.toolsCount} Active Tools</div>
          <div className={styles.metricLabel}>REST APIs, Web, SQL, Python</div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>
            <DatabaseIcon size={20} />
          </div>
          <div className={styles.metricVal}>{stats.memoriesCount} Vectors</div>
          <div className={styles.metricLabel}>Long-Term Semantic Memory</div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>
            <TerminalIcon size={20} />
          </div>
          <div className={styles.metricVal}>{stats.workflowsCount} Workflows</div>
          <div className={styles.metricLabel}>Autonomous Executions</div>
        </div>
      </div>

      {/* Roadmap & Phases Status */}
      <div className={styles.phasesSection}>
        <h3>System Phases Status</h3>
        <div className={styles.phasesGrid}>
          <div className={styles.phaseCard}>
            <span className={styles.phaseBadgeComplete}>
              <CheckIcon size={12} /> Phase 1
            </span>
            <h4>Core Architecture</h4>
            <p>FastAPI, Flask integration, SQLite relational store, Docker, and schema definitions.</p>
          </div>
          <div className={styles.phaseCard}>
            <span className={styles.phaseBadgeComplete}>
              <CheckIcon size={12} /> Phase 2
            </span>
            <h4>Intelligence Layer</h4>
            <p>Hugging Face Serverless Router, dynamic prompt engineering, and ReAct multi-step reasoning.</p>
          </div>
          <div className={styles.phaseCard}>
            <span className={styles.phaseBadgeComplete}>
              <CheckIcon size={12} /> Phase 3
            </span>
            <h4>Tools & Actions</h4>
            <p>REST API Caller, BeautifulSoup Web Scraper, DuckDuckGo Search, SQLite Database Tool, Code Sandbox.</p>
          </div>
          <div className={styles.phaseCard}>
            <span className={styles.phaseBadgeComplete}>
              <CheckIcon size={12} /> Phase 4
            </span>
            <h4>Memory System</h4>
            <p>Sliding context window buffer, Hugging Face Vector DB (MiniLM-L6-v2), and conversation history.</p>
          </div>
          <div className={styles.phaseCard}>
            <span className={styles.phaseBadgeComplete}>
              <CheckIcon size={12} /> Phase 5
            </span>
            <h4>Frontend</h4>
            <p>Kimi AI-inspired minimalist dark theme, Agent Workspace side panel, rounded composer, and SSE streaming.</p>
          </div>
          <div className={styles.phaseCard}>
            <span className={styles.phaseBadgeComplete}>
              <CheckIcon size={12} /> Phase 6
            </span>
            <h4>Advanced AI</h4>
            <p>Multi-Agent Swarm (Supervisor, Researcher, Coder, SQL, Reviewer), Autonomous Workflows, Voice & Vision.</p>
          </div>
        </div>
      </div>

      {/* Live Tool Execution Feed */}
      <div className={styles.feedSection}>
        <h3>Recent Tool Execution Activity</h3>
        {toolLogs.length === 0 ? (
          <div className={styles.emptyFeed}>No tools executed yet. Start asking questions in Chat.</div>
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.logsTable}>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Tool Name</th>
                  <th>Status</th>
                  <th>Latency</th>
                  <th>Parameters</th>
                  <th>Output Snippet</th>
                </tr>
              </thead>
              <tbody>
                {toolLogs.slice(0, 10).map((log) => (
                  <tr key={log.id}>
                    <td>{new Date(log.created_at).toLocaleTimeString()}</td>
                    <td>
                      <span className={styles.toolNameCell}>{log.tool_name}</span>
                    </td>
                    <td>
                      <span className={log.status === "success" ? styles.statusSuccess : styles.statusError}>
                        {log.status}
                      </span>
                    </td>
                    <td>{log.duration_ms} ms</td>
                    <td className={log.input_params ? styles.codeSnippetCell : ""}>
                      {log.input_params?.slice(0, 50)}...
                    </td>
                    <td className={styles.codeSnippetCell}>
                      {log.output_result?.slice(0, 60)}...
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
