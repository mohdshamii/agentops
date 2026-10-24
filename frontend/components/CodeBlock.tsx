"use client";

import { useState } from "react";
import { CopyIcon, CheckIcon, TerminalIcon } from "./Icons";
import styles from "@/styles/chat.module.css";

interface Props {
  node?: any;
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
}

export default function CodeBlock({ inline, className, children, ...props }: Props) {
  const [copied, setCopied] = useState(false);
  const match = /language-(\w+)/.exec(className || "");
  const lang = match ? match[1] : "text";
  const codeString = String(children).replace(/\n$/, "");

  const handleCopy = () => {
    navigator.clipboard.writeText(codeString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Detect true inline code (either inline prop is true, or no language className and single line without newline)
  const isInline = inline || (!className && !codeString.includes("\n"));

  if (isInline) {
    return (
      <code className={styles.inlineCode} {...props}>
        {children}
      </code>
    );
  }

  return (
    <div className={styles.codeBlockWrapper}>
      <div className={styles.codeHeader}>
        <div className={styles.codeHeaderLeft}>
          <TerminalIcon size={12} className={styles.terminalIcon} />
          <span className={styles.codeLang}>{lang}</span>
        </div>
        <button onClick={handleCopy} className={styles.copyBtn} title="Copy Code">
          {copied ? (
            <>
              <CheckIcon size={12} />
              <span>Copied</span>
            </>
          ) : (
            <>
              <CopyIcon size={12} />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className={styles.codePre}>
        <code className="font-mono">{codeString}</code>
      </pre>
    </div>
  );
}
