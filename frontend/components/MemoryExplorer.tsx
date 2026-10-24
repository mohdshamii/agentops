"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import { MemoryItem } from "@/lib/types";
import { SearchIcon, DatabaseIcon, PlusIcon, CloseIcon } from "./Icons";
import styles from "@/styles/chat.module.css";

export default function MemoryExplorer() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [newContent, setNewContent] = useState("");
  const [newCategory, setNewCategory] = useState("user_preference");
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    loadMemories();
  }, []);

  const loadMemories = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getMemories();
      setMemories(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearching(true);
    try {
      const res = await apiClient.searchMemories(searchQuery.trim(), 5);
      setSearchResults(res.matches || []);
    } catch (e) {
      console.error(e);
    } finally {
      setSearching(false);
    }
  };

  const handleAddMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newContent.trim()) return;

    try {
      await apiClient.createMemory(newContent.trim(), newCategory);
      setNewContent("");
      loadMemories();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteMemory = async (id: string) => {
    try {
      await apiClient.deleteMemory(id);
      setMemories((prev) => prev.filter((m) => m.id !== id));
      setSearchResults((prev) => prev.filter((m) => m.id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className={styles.memoryContainer}>
      <div className={styles.memoryHeader}>
        <h2>Vector Memory System (Long-Term & Semantic Store)</h2>
        <p>
          Powered by Hugging Face <code>sentence-transformers/all-MiniLM-L6-v2</code> embeddings.
          Relevant memories are automatically retrieved and injected into the agent's reasoning context.
        </p>
      </div>

      <div className={styles.memoryGrid}>
        {/* Left Column: Semantic Search & Add Memory */}
        <div className={styles.memoryActionsCol}>
          {/* Semantic Search Box */}
          <div className={styles.actionCard}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.4rem" }}>
              <SearchIcon size={16} />
              <h3 style={{ margin: 0 }}>Semantic Vector Search</h3>
            </div>
            <p className={styles.subtext}>Test cosine similarity retrieval across embeddings</p>
            <form onSubmit={handleSearch}>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="E.g. What frameworks are we using?"
                className={styles.inputField}
              />
              <button type="submit" disabled={searching || !searchQuery.trim()} className={styles.actionBtn}>
                {searching ? "Calculating Cosine Similarity..." : "Search Vector Space"}
              </button>
            </form>

            {searchResults.length > 0 && (
              <div className={styles.searchResultsBox}>
                <h4>Top Semantic Matches:</h4>
                {searchResults.map((m) => (
                  <div key={m.id} className={styles.searchResultItem}>
                    <div className={styles.resultMeta}>
                      <span className={styles.similarityScore}>
                        Similarity: {(m.similarity * 100).toFixed(1)}%
                      </span>
                      <span className={styles.categoryPill}>{m.category}</span>
                    </div>
                    <p className={styles.resultText}>{m.content}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Add Memory Box */}
          <div className={styles.actionCard}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.4rem" }}>
              <PlusIcon size={16} />
              <h3 style={{ margin: 0 }}>Store New Long-Term Memory</h3>
            </div>
            <form onSubmit={handleAddMemory}>
              <textarea
                value={newContent}
                onChange={(e) => setNewContent(e.target.value)}
                placeholder="Enter fact, preference, or system instruction to remember..."
                className={styles.textareaField}
                rows={3}
                required
              />
              <div className={styles.categorySelectRow}>
                <label>Category:</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className={styles.selectInput}
                >
                  <option value="user_preference">User Preference</option>
                  <option value="user_fact">User Fact</option>
                  <option value="system_knowledge">System Knowledge</option>
                  <option value="agent_experience">Agent Experience</option>
                </select>
              </div>
              <button type="submit" disabled={!newContent.trim()} className={styles.actionBtn}>
                Store in Vector Database
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Stored Memory Items */}
        <div className={styles.memoryListCol}>
          <div className={styles.listCard}>
            <div className={styles.listHeader}>
              <h3>Stored Memories ({memories.length})</h3>
              <button onClick={loadMemories} className={styles.miniRefreshBtn}>
                Refresh
              </button>
            </div>

            {loading ? (
              <div className={styles.loadingText}>Loading vector memories...</div>
            ) : memories.length === 0 ? (
              <div className={styles.emptyText}>No memories stored yet. Add one using the form on the left.</div>
            ) : (
              <div className={styles.memoriesScrollList}>
                {memories.map((mem) => (
                  <div key={mem.id} className={styles.memoryCardItem}>
                    <div className={styles.memoryCardHeader}>
                      <span className={styles.categoryPill}>{mem.category}</span>
                      <button
                        onClick={() => handleDeleteMemory(mem.id)}
                        className={styles.deleteMemBtn}
                        title="Delete memory"
                      >
                        <CloseIcon size={12} />
                      </button>
                    </div>
                    <p className={styles.memoryContentText}>{mem.content}</p>
                    <span className={styles.memoryIdSnippet}>ID: {mem.id.slice(0, 12)}...</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
