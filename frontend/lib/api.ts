import axios, { AxiosInstance } from "axios";
import {
  ChatRequest,
  ChatResponse,
  Conversation,
  ToolItem,
  MemoryItem,
  WorkflowItem,
  AgentRole
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }

  async healthCheck() {
    const response = await this.client.get("/health/");
    return response.data;
  }

  // --- Chat & Real-Time Responses ---
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.client.post("/api/chat/send", request);
    return response.data;
  }

  streamMessage(
    request: ChatRequest,
    callbacks: {
      onInit?: (data: { conversation_id: string; message_id: string }) => void;
      onTrace?: (trace: any[]) => void;
      onToken?: (token: string) => void;
      onDone?: (data: { tokens_used: number; model: string }) => void;
      onError?: (err: any) => void;
    }
  ) {
    const url = `${API_BASE_URL}/api/chat/stream`;
    
    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    })
      .then(async (response) => {
        if (!response.body) {
          throw new Error("ReadableStream not supported");
        }
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.substring(6));
                if (data.type === "init" && callbacks.onInit) callbacks.onInit(data);
                if (data.type === "reasoning_trace" && callbacks.onTrace) callbacks.onTrace(data.trace);
                if (data.type === "token" && callbacks.onToken) callbacks.onToken(data.token);
                if (data.type === "done" && callbacks.onDone) callbacks.onDone(data);
              } catch (e) {
                // Ignore parse errors on incomplete chunks
              }
            }
          }
        }
      })
      .catch((err) => {
        if (callbacks.onError) callbacks.onError(err);
      });
  }

  async generateCode(prompt: string) {
    const response = await this.client.post("/api/chat/generate-code", {
      message: prompt,
    });
    return response.data;
  }

  // --- Conversations ---
  async getConversations(): Promise<Conversation[]> {
    const response = await this.client.get("/api/conversations/");
    return response.data;
  }

  async getConversation(id: string): Promise<Conversation> {
    const response = await this.client.get(`/api/conversations/${id}`);
    return response.data;
  }

  async createConversation(): Promise<Conversation> {
    const response = await this.client.post("/api/conversations/create");
    return response.data;
  }

  async deleteConversation(id: string) {
    const response = await this.client.delete(`/api/conversations/${id}`);
    return response.data;
  }

  // --- Tools & Actions ---
  async getTools(): Promise<ToolItem[]> {
    const response = await this.client.get("/api/tools/");
    return response.data;
  }

  async executeTool(tool_name: string, params: any) {
    const response = await this.client.post("/api/tools/execute", {
      tool_name,
      params,
    });
    return response.data;
  }

  async getToolLogs() {
    const response = await this.client.get("/api/tools/logs");
    return response.data;
  }

  // --- Memory System ---
  async getMemories(): Promise<MemoryItem[]> {
    const response = await this.client.get("/api/memory/");
    return response.data;
  }

  async createMemory(content: string, category: string = "general", metadata: any = {}) {
    const response = await this.client.post("/api/memory/create", {
      content,
      category,
      metadata,
    });
    return response.data;
  }

  async searchMemories(query: string, top_k: number = 4) {
    const response = await this.client.post("/api/memory/search", {
      query,
      top_k,
    });
    return response.data;
  }

  async deleteMemory(id: string) {
    const response = await this.client.delete(`/api/memory/${id}`);
    return response.data;
  }

  // --- Multi-Agent System ---
  async getAgentsTeam(): Promise<{ agents: AgentRole[] }> {
    const response = await this.client.get("/api/agents/team");
    return response.data;
  }

  async runMultiAgentTask(task: string, agent_roles?: string[]) {
    const response = await this.client.post("/api/agents/run", {
      task,
      agent_roles,
    });
    return response.data;
  }

  // --- Autonomous Workflows ---
  async getWorkflows(): Promise<WorkflowItem[]> {
    const response = await this.client.get("/api/workflows/");
    return response.data;
  }

  async createWorkflow(title: string, goal: string) {
    const response = await this.client.post("/api/workflows/create", {
      title,
      goal,
    });
    return response.data;
  }

  async runWorkflow(id: string): Promise<WorkflowItem> {
    const response = await this.client.post(`/api/workflows/${id}/run`);
    return response.data;
  }

  // --- Vision & Voice ---
  async analyzeImage(image_base64: string, prompt?: string) {
    const response = await this.client.post("/api/vision/analyze", {
      image_base64,
      prompt,
    });
    return response.data;
  }

  async transcribeVoice(audio_base64: string) {
    const response = await this.client.post("/api/voice/transcribe", {
      audio_base64,
    });
    return response.data;
  }
}

export const apiClient = new APIClient();