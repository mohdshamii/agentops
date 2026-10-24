"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import { DatabaseIcon, TerminalIcon, SpinnerIcon } from "./Icons";
import styles from "@/styles/chat.module.css";

export default function DatabaseExplorer() {
  const [schemaInfo, setSchemaInfo] = useState<any>(null);
  const [sqlQuery, setSqlQuery] = useState("SELECT * FROM conversations LIMIT 10;");
  const [queryResult, setQueryResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadSchema();
    handleRunQuery("SELECT * FROM conversations LIMIT 10;");
  }, []);

  const loadSchema = async () => {
    try {
      const res = await apiClient.executeTool("database_query", { query: "SHOW_TABLES" });
      if (res && res.result) {
        setSchemaInfo(res.result);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleRunQuery = async (customQuery?: string) => {
    const q = customQuery || sqlQuery;
    if (!q.trim()) return;

    setLoading(true);
    setError("");
    try {
      const res = await apiClient.executeTool("database_query", { query: q });
      if (res && res.result) {
        if (res.result.status === "error") {
          setError(res.result.message);
          setQueryResult(null);
        } else {
          setQueryResult(res.result);
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to execute SQL query");
      setQueryResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.dbContainer}>
      <div className={styles.dbHeader}>
        <h2>Relational Database Explorer (SQLite & SQLAlchemy)</h2>
        <p>Inspect database schemas, view conversation records, and test SQL queries safely.</p>
      </div>

      <div className={styles.dbLayoutGrid}>
        {/* Left: Schema Browser & Quick Queries */}
        <div className={styles.dbSchemaCol}>
          <div className={styles.actionCard}>
            <h3>Active Tables & Schemas</h3>
            {schemaInfo?.tables ? (
              <div className={styles.tablesList}>
                {schemaInfo.tables.map((tbl: string) => (
                  <div key={tbl} className={styles.tableSchemaItem}>
                    <div
                      className={styles.tableNameRow}
                      onClick={() => {
                        const q = `SELECT * FROM ${tbl} LIMIT 10;`;
                        setSqlQuery(q);
                        handleRunQuery(q);
                      }}
                    >
                      <span style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
                        <DatabaseIcon size={14} /> <strong>{tbl}</strong>
                      </span>
                      <button className={styles.miniQueryBtn}>Query</button>
                    </div>
                    {schemaInfo.schemas?.[tbl] && (
                      <div className={styles.colsList}>
                        {schemaInfo.schemas[tbl].map((c: any) => (
                          <span key={c.name} className={styles.colBadge}>
                            {c.name}: {c.type}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className={styles.loadingText}>Loading schema...</div>
            )}
          </div>
        </div>

        {/* Right: SQL Query Runner & Results */}
        <div className={styles.dbQueryCol}>
          <div className={styles.actionCard}>
            <h3>SQL Query Runner</h3>
            <div className={styles.sqlEditorBox}>
              <textarea
                value={sqlQuery}
                onChange={(e) => setSqlQuery(e.target.value)}
                placeholder="Enter SQL query (e.g. SELECT * FROM messages;)"
                className={styles.sqlTextarea}
                rows={3}
              />
              <div className={styles.sqlActionRow}>
                <button
                  onClick={() => handleRunQuery()}
                  disabled={loading || !sqlQuery.trim()}
                  className={styles.actionBtn}
                >
                  {loading ? (
                    <span style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
                      <SpinnerIcon size={14} /> Executing...
                    </span>
                  ) : (
                    "Run SQL Query"
                  )}
                </button>
              </div>
            </div>

            {error && <div className={styles.error}>{error}</div>}

            {queryResult && (
              <div className={styles.queryResultsSection}>
                <h4>
                  Query Results:{" "}
                  {queryResult.row_count !== undefined
                    ? `${queryResult.row_count} rows`
                    : queryResult.message || "Executed"}
                </h4>

                {queryResult.rows && queryResult.rows.length > 0 ? (
                  <div className={styles.tableWrapper}>
                    <table className={styles.logsTable}>
                      <thead>
                        <tr>
                          {queryResult.columns?.map((col: string) => (
                            <th key={col}>{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {queryResult.rows.map((row: any, rIdx: number) => (
                          <tr key={rIdx}>
                            {queryResult.columns?.map((col: string) => (
                              <td key={col} className={styles.codeSnippetCell}>
                                {String(row[col] ?? "")}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className={styles.emptyFeed}>No rows returned.</div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
