"use client";

import styles from "@/styles/chat.module.css";
import { BotIcon } from "./Icons";

interface Props {
  activeTab: string;
  onSelectTab: (tab: string) => void;
}

export default function Header({ activeTab, onSelectTab }: Props) {
  const tabs = [
    { id: "chat", label: "Chat UI" },
    { id: "dashboard", label: "Operations Dashboard" },
    { id: "workflows", label: "Autonomous Workflows" },
    { id: "multi_agent", label: "Multi-Agent Swarm" },
    { id: "memory", label: "Vector Memory" },
    { id: "database", label: "Database Explorer" }
  ];

  return (
    <header className={styles.appHeader}>
      <div className={styles.headerBrand}>
        <div className={styles.logoBadge}>
          <BotIcon size={16} />
        </div>
        <div className={styles.brandText}>
          <h1>AgentOps</h1>
          <span className={styles.brandSub}>Hugging Face Agentic AI Platform</span>
        </div>
      </div>

      <nav className={styles.headerNav}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onSelectTab(tab.id)}
            className={`${styles.navTabBtn} ${activeTab === tab.id ? styles.navTabActive : ""}`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <div className={styles.headerStatus}>
        <span className={styles.statusDot}></span>
        <span className={styles.statusText}>HF Router Online</span>
      </div>
    </header>
  );
}
