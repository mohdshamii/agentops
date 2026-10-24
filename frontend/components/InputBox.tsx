"use client";

import { useState, useRef, useEffect } from "react";
import styles from "@/styles/chat.module.css";
import { ImageIcon, MicIcon, CloseIcon, SendIcon } from "./Icons";

interface Props {
  onSend: (message: string, imageBase64?: string, audioBase64?: string) => void;
  disabled?: boolean;
}

export default function InputBox({ onSend, disabled }: Props) {
  const [text, setText] = useState("");
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);

  // Initialize Web Speech API for voice input
  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = "en-US";

        recognition.onresult = (event: any) => {
          let transcript = "";
          for (let i = 0; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
          }
          setText((prev) => (prev ? `${prev} ${transcript}` : transcript));
        };

        recognition.onerror = () => {
          setIsListening(false);
        };

        recognition.onend = () => {
          setIsListening(false);
        };

        recognitionRef.current = recognition;
      }
    }
  }, []);

  const handleToggleVoice = () => {
    if (!recognitionRef.current) {
      alert("Speech recognition is not supported in this browser. Please use Google Chrome or Edge.");
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (err) {
        setIsListening(false);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if ((!text.trim() && !imagePreview) || disabled) return;

    onSend(text.trim(), imagePreview || undefined);
    setText("");
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className={styles.inputBoxContainer}>
      {imagePreview && (
        <div className={styles.imagePreviewBar}>
          <img src={imagePreview} alt="Attached preview" className={styles.previewThumb} />
          <button
            type="button"
            onClick={() => setImagePreview(null)}
            className={styles.removeImageBtn}
          >
            <CloseIcon size={12} />
          </button>
          <span className={styles.previewLabel}>Vision Asset Attached</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className={styles.inputForm}>
        {/* Hidden Image File Input */}
        <input
          type="file"
          ref={fileInputRef}
          accept="image/*"
          onChange={handleFileChange}
          style={{ display: "none" }}
        />

        {/* Vision Attachment Button */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className={styles.toolActionBtn}
          title="Attach Image (Vision Support)"
          disabled={disabled}
        >
          <ImageIcon size={16} />
        </button>

        {/* Voice Input Button */}
        <button
          type="button"
          onClick={handleToggleVoice}
          className={`${styles.toolActionBtn} ${isListening ? styles.listeningActive : ""}`}
          title={isListening ? "Listening... Click to stop" : "Voice Input (Speech-to-Text)"}
          disabled={disabled}
        >
          <MicIcon size={16} />
        </button>

        {/* Text Input Area */}
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            isListening
              ? "Listening to your voice..."
              : "Ask AgentOps anything... (Type, attach image, or speak)"
          }
          className={styles.textareaInput}
          rows={1}
          disabled={disabled}
        />

        {/* Send Button */}
        <button
          type="submit"
          disabled={(!text.trim() && !imagePreview) || disabled}
          className={styles.sendButton}
        >
          <span>Send</span>
          <SendIcon size={14} />
        </button>
      </form>
    </div>
  );
}
