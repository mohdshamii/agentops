"use client";

import { useState, useRef, useEffect } from "react";
import {
  SendIcon,
  GlobeIcon,
  PaperclipIcon,
  ChevronDownIcon,
  CloseIcon,
  SpinnerIcon
} from "./Icons";
import { MODELS } from "@/lib/constants";
import styles from "@/styles/composer.module.css";

interface Props {
  onSend: (message: string, imageBase64?: string, options?: { enableSearch?: boolean; model?: string }) => void;
  disabled?: boolean;
  activeModel: string;
  onSelectModel: (model: string) => void;
}

export default function PromptComposer({
  onSend,
  disabled = false,
  activeModel,
  onSelectModel
}: Props) {
  const [text, setText] = useState("");
  const [enableWebSearch, setEnableWebSearch] = useState(false);
  const [showModelMenu, setShowModelMenu] = useState(false);
  const [attachedImage, setAttachedImage] = useState<string | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const modelMenuRef = useRef<HTMLDivElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [text]);

  // Close model menu when clicking outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (modelMenuRef.current && !modelMenuRef.current.contains(e.target as Node)) {
        setShowModelMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        setAttachedImage(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if ((!text.trim() && !attachedImage) || disabled) return;

    onSend(text.trim(), attachedImage || undefined, {
      enableSearch: enableWebSearch,
      model: activeModel
    });

    setText("");
    setAttachedImage(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const currentModelObj = MODELS.find((m) => m.id === activeModel) || MODELS[0];
  const shortModelName = currentModelObj.name.split("-")[0].trim();

  return (
    <div className={styles.composerWrapper}>
      <div className={styles.composerCard}>
        {/* Attached Asset Chip */}
        {attachedImage && (
          <div className={styles.attachmentChip}>
            <img src={attachedImage} alt="Attachment" className={styles.thumbImage} />
            <span className={styles.attachmentLabel}>Asset Attached</span>
            <button
              type="button"
              onClick={() => setAttachedImage(null)}
              className={styles.removeAssetBtn}
            >
              <CloseIcon size={12} />
            </button>
          </div>
        )}

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question, analyze data, or execute an autonomous mission..."
          className={styles.textarea}
          rows={1}
          disabled={disabled}
        />

        {/* Toolbar Bar */}
        <div className={styles.toolbarRow}>
          <div className={styles.leftPillsGroup}>
            {/* Model Selector Pill */}
            <div className={styles.modelSelectorContainer} ref={modelMenuRef}>
              <button
                type="button"
                onClick={() => setShowModelMenu(!showModelMenu)}
                className={styles.pillButton}
                title="Select Language Model"
              >
                <span>{shortModelName}</span>
                <ChevronDownIcon size={12} />
              </button>

              {showModelMenu && (
                <div className={styles.modelDropdownMenu}>
                  <div className={styles.dropdownHeader}>Select Agent Model</div>
                  {MODELS.map((m) => (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => {
                        onSelectModel(m.id);
                        setShowModelMenu(false);
                      }}
                      className={`${styles.modelOptionItem} ${
                        activeModel === m.id ? styles.modelOptionActive : ""
                      }`}
                    >
                      <span className={styles.modelOptionName}>{m.name}</span>
                      <span className={styles.modelOptionId}>{m.id}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Web Search Toggle Pill */}
            <button
              type="button"
              onClick={() => setEnableWebSearch(!enableWebSearch)}
              className={`${styles.pillButton} ${
                enableWebSearch ? styles.pillButtonActive : ""
              }`}
              title="Toggle Live Web Search"
            >
              <GlobeIcon size={14} />
              <span>Search Web</span>
            </button>

            {/* Upload File Button */}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className={styles.pillIconButton}
              title="Attach File or Image"
              disabled={disabled}
            >
              <PaperclipIcon size={15} />
            </button>
            <input
              type="file"
              ref={fileInputRef}
              accept="image/*,text/*,application/json"
              onChange={handleFileSelect}
              style={{ display: "none" }}
            />
          </div>

          {/* Submit Action Button */}
          <div className={styles.rightActionGroup}>
            <button
              type="button"
              onClick={() => handleSubmit()}
              disabled={(!text.trim() && !attachedImage) || disabled}
              className={styles.sendButton}
              title="Send message (Enter)"
            >
              {disabled ? <SpinnerIcon size={16} /> : <SendIcon size={16} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
