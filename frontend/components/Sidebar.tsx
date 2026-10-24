"use client";

import { useState } from "react";
import {
  LogoIcon,
  PlusIcon,
  SearchIcon,
  TrashIcon,
  SidebarToggleIcon,
  SunIcon,
  MoonIcon,
  WorkspaceIcon,
  ToolIcon,
  BrainIcon,
  DatabaseIcon
} from "./Icons";
import { Conversation } from "@/lib/types";
import styles from "@/styles/sidebar.module.css";

interface Props {
  isOpen: boolean;
  onToggle: () => void;
  conversations: Conversation[];
  activeConversationId?: string;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string, e: React.MouseEvent) => void;
  isWorkspaceOpen: boolean;
  onToggleWorkspace: () => void;
  activeView: string;
  onSelectView: (view: string) => void;
}

export default function Sidebar({
  isOpen,
  onToggle,
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  isWorkspaceOpen,
  onToggleWorkspace,
  activeView,
  onSelectView
}: Props) {
  const [searchQuery, setSearchQuery] = useState("");
  const [isDarkTheme, setIsDarkTheme] = useState(true);

  const toggleTheme = () => {
    const nextTheme = !isDarkTheme;
    setIsDarkTheme(nextTheme);
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("data-theme", nextTheme ? "dark" : "light");
    }
  };

  const filtered = conversations.filter((c) =>
    (c.title || "New Chat").toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <aside className={`${styles.sidebar} ${isOpen ? styles.sidebarOpen : styles.sidebarClosed}`}>
      {/* Brand & Collapse Header */}
      <div className={styles.sidebarHeader}>
        <div className={styles.brandGroup} onClick={() => onSelectView("chat")} style={{ cursor: "pointer" }}>
          <LogoIcon size={22} className={styles.brandLogo} />
          <span className={styles.brandName}>AgentOps</span>
          <span className={styles.brandTag}>AI</span>
        </div>
        <button onClick={onToggle} className={styles.toggleBtn} title="Toggle Sidebar">
          <SidebarToggleIcon size={16} />
        </button>
      </div>

      {/* New Chat Button */}
      <div className={styles.actionRow}>
        <button
          onClick={() => {
            onSelectView("chat");
            onNewConversation();
          }}
          className={styles.newChatBtn}
        >
          <PlusIcon size={14} />
          <span>New Chat</span>
        </button>
      </div>

      {/* Navigation Views */}
      <div className={styles.viewsNav}>
        <button
          onClick={() => onSelectView("chat")}
          className={`${styles.viewBtn} ${activeView === "chat" ? styles.viewBtnActive : ""}`}
        >
          <LogoIcon size={14} />
          <span>Chat Stream</span>
        </button>
        <button
          onClick={() => onSelectView("dashboard")}
          className={`${styles.viewBtn} ${activeView === "dashboard" ? styles.viewBtnActive : ""}`}
        >
          <ToolIcon size={14} />
          <span>Dashboard & Telemetry</span>
        </button>
        <button
          onClick={() => onSelectView("workflows")}
          className={`${styles.viewBtn} ${activeView === "workflows" ? styles.viewBtnActive : ""}`}
        >
          <BrainIcon size={14} />
          <span>Autonomous Workflows</span>
        </button>
        <button
          onClick={() => onSelectView("database")}
          className={`${styles.viewBtn} ${activeView === "database" ? styles.viewBtnActive : ""}`}
        >
          <DatabaseIcon size={14} />
          <span>Database Explorer</span>
        </button>
      </div>

      {/* Search Input */}
      <div className={styles.searchWrapper}>
        <SearchIcon size={13} className={styles.searchIcon} />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search chats..."
          className={styles.searchInput}
        />
      </div>

      {/* Chat History List */}
      <div className={styles.historyList}>
        <div className={styles.sectionHeader}>Recent Conversations</div>
        {filtered.length === 0 ? (
          <div className={styles.emptyNotice}>
            {searchQuery ? "No matches found." : "No previous chats."}
          </div>
        ) : (
          filtered.map((conv) => {
            const isActive = activeView === "chat" && activeConversationId === conv.id;
            return (
              <div
                key={conv.id}
                onClick={() => {
                  onSelectView("chat");
                  onSelectConversation(conv.id);
                }}
                className={`${styles.convItem} ${isActive ? styles.convItemActive : ""}`}
              >
                <span className={styles.convTitle}>{conv.title || "New Conversation"}</span>
                <button
                  type="button"
                  onClick={(e) => onDeleteConversation(conv.id, e)}
                  className={styles.deleteBtn}
                  title="Delete chat"
                >
                  <TrashIcon size={12} />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Sidebar Footer */}
      <div className={styles.sidebarFooter}>
        <button
          type="button"
          onClick={onToggleWorkspace}
          className={`${styles.footerActionBtn} ${isWorkspaceOpen ? styles.footerActionActive : ""}`}
          title="Toggle Agent Workspace Side Panel"
        >
          <WorkspaceIcon size={15} />
          <span>Agent Workspace</span>
        </button>

        <button
          type="button"
          onClick={toggleTheme}
          className={styles.footerActionBtn}
          title={isDarkTheme ? "Switch to Light Theme" : "Switch to Dark Theme"}
        >
          {isDarkTheme ? <SunIcon size={15} /> : <MoonIcon size={15} />}
          <span>{isDarkTheme ? "Light Theme" : "Dark Theme"}</span>
        </button>
      </div>
    </aside>
  );
}
