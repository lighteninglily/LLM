"use client";

import { useEffect, useRef, useState } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
  type ThreadMessage,
} from "@assistant-ui/react";
import { Thread } from "@assistant-ui/react";
import { makeMarkdownText } from "@assistant-ui/react-markdown";

const MarkdownText = makeMarkdownText();

interface HybridResponse {
  answer: string;
  source: "sql" | "rag";
  sql_query?: string;
  data?: any[];
  row_count?: number;
  rag_sources?: string[];
  error?: string;
}

const createHybridAdapter = (apiUrl: string): ChatModelAdapter => ({
  async *run({ messages, abortSignal }) {
    const lastMessage = messages[messages.length - 1];
    const question = lastMessage.content
      .filter((c): c is { type: "text"; text: string } => c.type === "text")
      .map((c) => c.text)
      .join("\n");

    try {
      const response = await fetch(`${apiUrl}/api/hybrid/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
        signal: abortSignal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: HybridResponse = await response.json();
      
      // Build response with metadata
      let responseText = data.answer || "No response received.";
      
      // Add source indicator
      if (data.source === "sql" && data.sql_query) {
        responseText += `\n\n---\n**Source:** SQL Query (${data.row_count || 0} rows)\n\`\`\`sql\n${data.sql_query}\n\`\`\``;
      } else if (data.source === "rag" && data.rag_sources?.length) {
        responseText += `\n\n---\n**Source:** RAG\n**Documents:** ${data.rag_sources.join(", ")}`;
      }

      yield {
        content: [{ type: "text" as const, text: responseText }],
      };
    } catch (error) {
      yield {
        content: [
          {
            type: "text" as const,
            text: `Error: ${error instanceof Error ? error.message : "Unknown error"}`,
          },
        ],
      };
    }
  },
});

function ChatInterface({ apiUrl }: { apiUrl: string }) {
  const adapter = createHybridAdapter(apiUrl);
  const runtime = useLocalRuntime(adapter);

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="h-full flex flex-col bg-gray-950">
        <Thread
          welcome={{
            suggestions: [
              { text: "What did MMW produce in November 2025?", prompt: "What did MMW produce in November 2025?" },
              { text: "Compare galv line 1 and 2 production", prompt: "Compare galv line 1 and 2 production" },
              { text: "Show total sales by customer last month", prompt: "Show total sales by customer last month" },
              { text: "What is the company policy on leave?", prompt: "What is the company policy on leave?" },
            ],
          }}
          assistantMessage={{
            components: {
              Text: MarkdownText,
            },
          }}
        />
      </div>
    </AssistantRuntimeProvider>
  );
}

export function AssistantChat({ apiUrl = "http://localhost:8080" }: { apiUrl?: string }) {
  return <ChatInterface apiUrl={apiUrl} />;
}
