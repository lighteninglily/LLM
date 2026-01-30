"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Database, BookOpen, Loader2, ChevronDown, ChevronUp } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  source?: "sql" | "rag";
  sqlQuery?: string;
  data?: any[];
  rowCount?: number;
  ragSources?: string[];
  timestamp: Date;
}

interface HybridChatProps {
  apiUrl?: string;
}

export function HybridChat({ apiUrl = "http://localhost:8080" }: HybridChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const toggleExpanded = (messageId: string) => {
    setExpandedMessages((prev) => {
      const next = new Set(prev);
      if (next.has(messageId)) {
        next.delete(messageId);
      } else {
        next.add(messageId);
      }
      return next;
    });
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch(`${apiUrl}/api/hybrid/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMessage.content }),
      });

      const data = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.answer || "No response received.",
        source: data.source,
        sqlQuery: data.sql_query,
        data: data.data,
        rowCount: data.row_count,
        ragSources: data.rag_sources,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Error: ${error instanceof Error ? error.message : "Failed to get response"}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-900 rounded-lg border border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-blue-400" />
          <span className="font-semibold text-white">Hybrid Query Assistant</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span className="flex items-center gap-1">
            <Database className="w-3 h-3 text-green-400" /> SQL
          </span>
          <span className="text-gray-600">+</span>
          <span className="flex items-center gap-1">
            <BookOpen className="w-3 h-3 text-purple-400" /> RAG
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <Database className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium">Ask me anything about your data</p>
            <p className="text-sm mt-2">
              Data queries use SQL • Knowledge queries use RAG
            </p>
            <div className="mt-6 space-y-2 text-sm text-left max-w-md mx-auto">
              <p className="text-gray-400">Try asking:</p>
              <button
                onClick={() => setInput("What did CLIFFORD_MMW produce in November 2025?")}
                className="block w-full text-left px-3 py-2 bg-gray-800 rounded hover:bg-gray-700 transition"
              >
                "What did CLIFFORD_MMW produce in November 2025?"
              </button>
              <button
                onClick={() => setInput("Show total production by machine last month")}
                className="block w-full text-left px-3 py-2 bg-gray-800 rounded hover:bg-gray-700 transition"
              >
                "Show total production by machine last month"
              </button>
              <button
                onClick={() => setInput("Which products had the highest sales?")}
                className="block w-full text-left px-3 py-2 bg-gray-800 rounded hover:bg-gray-700 transition"
              >
                "Which products had the highest sales?"
              </button>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-4 py-3 ${
                message.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-800 text-gray-100"
              }`}
            >
              {/* Source badge for assistant messages */}
              {message.role === "assistant" && message.source && (
                <div className="flex items-center gap-2 mb-2">
                  {message.source === "sql" ? (
                    <span className="flex items-center gap-1 text-xs bg-green-900/50 text-green-400 px-2 py-0.5 rounded">
                      <Database className="w-3 h-3" /> SQL Query
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-xs bg-purple-900/50 text-purple-400 px-2 py-0.5 rounded">
                      <BookOpen className="w-3 h-3" /> RAG
                    </span>
                  )}
                  {message.rowCount !== undefined && (
                    <span className="text-xs text-gray-500">
                      {message.rowCount} rows
                    </span>
                  )}
                </div>
              )}

              {/* Message content */}
              <div className="whitespace-pre-wrap">{message.content}</div>

              {/* SQL Query expandable section */}
              {message.sqlQuery && (
                <div className="mt-3 border-t border-gray-700 pt-2">
                  <button
                    onClick={() => toggleExpanded(message.id)}
                    className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-300"
                  >
                    {expandedMessages.has(message.id) ? (
                      <ChevronUp className="w-3 h-3" />
                    ) : (
                      <ChevronDown className="w-3 h-3" />
                    )}
                    View SQL Query
                  </button>
                  {expandedMessages.has(message.id) && (
                    <pre className="mt-2 p-2 bg-gray-900 rounded text-xs text-green-400 overflow-x-auto">
                      {message.sqlQuery}
                    </pre>
                  )}
                </div>
              )}

              {/* Data table for SQL results */}
              {message.data && message.data.length > 0 && expandedMessages.has(message.id) && (
                <div className="mt-3 border-t border-gray-700 pt-2">
                  <p className="text-xs text-gray-400 mb-2">Data Preview (first 10 rows):</p>
                  <div className="overflow-x-auto">
                    <table className="text-xs w-full">
                      <thead>
                        <tr className="border-b border-gray-700">
                          {Object.keys(message.data[0]).map((key) => (
                            <th key={key} className="px-2 py-1 text-left text-gray-400">
                              {key}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {message.data.slice(0, 10).map((row, i) => (
                          <tr key={i} className="border-b border-gray-800">
                            {Object.values(row).map((val, j) => (
                              <td key={j} className="px-2 py-1">
                                {val !== null ? String(val) : "-"}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* RAG sources */}
              {message.ragSources && message.ragSources.length > 0 && (
                <div className="mt-3 border-t border-gray-700 pt-2">
                  <p className="text-xs text-gray-400">Sources:</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {message.ragSources.map((source, i) => (
                      <span
                        key={i}
                        className="text-xs bg-gray-700 px-2 py-0.5 rounded"
                      >
                        {source}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Timestamp */}
              <div className="text-xs text-gray-500 mt-2">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-lg px-4 py-3 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
              <span className="text-gray-400">Thinking...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-700 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about production, sales, inventory..."
            className="flex-1 bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg px-4 py-2 transition"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
