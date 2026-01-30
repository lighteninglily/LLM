"use client";

import { useState, useRef, useEffect, FormEvent } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Send,
  Database,
  BookOpen,
  Loader2,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Sparkles,
  User,
  Bot,
  RefreshCw,
  Settings,
} from "lucide-react";
import { RAGSettingsPanel } from "./rag-settings";
import { DataOverviewPanel } from "./data-overview";

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
  isStreaming?: boolean;
}

interface ChatUIProps {
  apiUrl?: string;
}

const SUGGESTIONS = [
  { text: "What did MMW produce in November 2025?", icon: Database },
  { text: "Compare galv line 1 and 2 production", icon: Database },
  { text: "What is the company leave policy?", icon: BookOpen },
  { text: "Show top 10 products by sales volume", icon: Database },
];

export function ChatUI({ apiUrl = "http://localhost:8080" }: ChatUIProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedSql, setExpandedSql] = useState<Set<string>>(new Set());
  const [showSettings, setShowSettings] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const copyToClipboard = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleSql = (id: string) => {
    setExpandedSql((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleSubmit = async (e?: FormEvent, overrideInput?: string) => {
    e?.preventDefault();
    const question = overrideInput || input.trim();
    if (!question || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: question,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    const assistantId = `assistant-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: assistantId,
        role: "assistant",
        content: "",
        timestamp: new Date(),
        isStreaming: true,
      },
    ]);

    try {
      const response = await fetch(`${apiUrl}/api/hybrid/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      const data = await response.json();

      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content: data.answer || "No response received.",
                source: data.source,
                sqlQuery: data.sql_query,
                data: data.data,
                rowCount: data.row_count,
                ragSources: data.rag_sources,
                isStreaming: false,
              }
            : m
        )
      );
    } catch (error) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content: `Error: ${error instanceof Error ? error.message : "Failed to get response"}`,
                isStreaming: false,
              }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="flex flex-col h-full bg-[#0a0a0a]">
      {/* Settings Panel */}
      <RAGSettingsPanel
        apiUrl={apiUrl}
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
      />

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-blue-400" />
          <span className="font-semibold text-white">Hybrid Query Assistant</span>
        </div>
        <button
          onClick={() => setShowSettings(true)}
          className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition"
          title="RAG Settings"
        >
          <Settings className="w-5 h-5" />
        </button>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full px-4 py-12">
            <div className="flex items-center gap-3 mb-8">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-semibold text-white">Hybrid Query Assistant</h1>
                <p className="text-gray-400 text-sm">SQL for data • RAG for knowledge</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl w-full">
              {SUGGESTIONS.map((suggestion, i) => (
                <button
                  key={i}
                  onClick={() => handleSubmit(undefined, suggestion.text)}
                  className="flex items-center gap-3 p-4 bg-[#1a1a1a] hover:bg-[#252525] border border-gray-800 rounded-xl text-left transition-all group"
                >
                  <suggestion.icon className="w-5 h-5 text-gray-500 group-hover:text-blue-400 transition-colors" />
                  <span className="text-gray-300 text-sm">{suggestion.text}</span>
                </button>
              ))}
            </div>

            {/* Data Overview */}
            <DataOverviewPanel apiUrl={apiUrl} />
          </div>
        ) : (
          <div className="max-w-3xl mx-auto py-6">
            {messages.map((message) => (
              <div key={message.id} className="group px-4 py-6 hover:bg-[#111]">
                <div className="flex gap-4">
                  {/* Avatar */}
                  <div className="flex-shrink-0">
                    {message.role === "user" ? (
                      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                        <User className="w-4 h-4 text-white" />
                      </div>
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                        <Bot className="w-4 h-4 text-white" />
                      </div>
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-white text-sm">
                        {message.role === "user" ? "You" : "Assistant"}
                      </span>
                      {message.source && (
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full ${
                            message.source === "sql"
                              ? "bg-green-900/50 text-green-400"
                              : "bg-purple-900/50 text-purple-400"
                          }`}
                        >
                          {message.source === "sql" ? (
                            <span className="flex items-center gap-1">
                              <Database className="w-3 h-3" /> SQL
                            </span>
                          ) : (
                            <span className="flex items-center gap-1">
                              <BookOpen className="w-3 h-3" /> RAG
                            </span>
                          )}
                        </span>
                      )}
                      {message.rowCount !== undefined && (
                        <span className="text-xs text-gray-500">
                          {message.rowCount} rows
                        </span>
                      )}
                    </div>

                    {message.isStreaming ? (
                      <div className="flex items-center gap-2 text-gray-400">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Thinking...</span>
                      </div>
                    ) : (
                      <div className="prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            code({ node, className, children, ...props }) {
                              const isInline = !className;
                              if (isInline) {
                                return (
                                  <code className="bg-gray-800 px-1.5 py-0.5 rounded text-sm" {...props}>
                                    {children}
                                  </code>
                                );
                              }
                              return (
                                <pre className="bg-[#1a1a1a] p-4 rounded-lg overflow-x-auto">
                                  <code className={className} {...props}>
                                    {children}
                                  </code>
                                </pre>
                              );
                            },
                            table({ children }) {
                              return (
                                <div className="overflow-x-auto my-4">
                                  <table className="min-w-full border-collapse">
                                    {children}
                                  </table>
                                </div>
                              );
                            },
                            th({ children }) {
                              return (
                                <th className="border border-gray-700 px-3 py-2 bg-gray-800 text-left text-sm font-medium">
                                  {children}
                                </th>
                              );
                            },
                            td({ children }) {
                              return (
                                <td className="border border-gray-700 px-3 py-2 text-sm">
                                  {children}
                                </td>
                              );
                            },
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    )}

                    {/* SQL Query Expandable */}
                    {message.sqlQuery && (
                      <div className="mt-4">
                        <button
                          onClick={() => toggleSql(message.id)}
                          className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 transition"
                        >
                          {expandedSql.has(message.id) ? (
                            <ChevronUp className="w-3 h-3" />
                          ) : (
                            <ChevronDown className="w-3 h-3" />
                          )}
                          View SQL Query
                        </button>
                        {expandedSql.has(message.id) && (
                          <pre className="mt-2 p-3 bg-[#1a1a1a] rounded-lg text-xs text-green-400 overflow-x-auto">
                            {message.sqlQuery}
                          </pre>
                        )}
                      </div>
                    )}

                    {/* RAG Sources */}
                    {message.ragSources && message.ragSources.length > 0 && (
                      <div className="mt-4 flex flex-wrap gap-2">
                        <span className="text-xs text-gray-500">Sources:</span>
                        {message.ragSources.map((source, i) => (
                          <span
                            key={i}
                            className="text-xs bg-gray-800 px-2 py-1 rounded"
                          >
                            {source}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Actions */}
                    {message.role === "assistant" && !message.isStreaming && (
                      <div className="flex items-center gap-2 mt-4 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => copyToClipboard(message.content, message.id)}
                          className="p-1.5 text-gray-500 hover:text-gray-300 hover:bg-gray-800 rounded transition"
                          title="Copy"
                        >
                          {copiedId === message.id ? (
                            <Check className="w-4 h-4 text-green-400" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-800 bg-[#0a0a0a] p-4">
        <div className="max-w-3xl mx-auto">
          <form onSubmit={handleSubmit} className="relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about production, sales, inventory, or company policies..."
              rows={1}
              className="w-full bg-[#1a1a1a] border border-gray-700 rounded-xl px-4 py-3 pr-12 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 resize-none"
              style={{ minHeight: "48px", maxHeight: "200px" }}
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-2 bottom-2 p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </form>

          <div className="flex items-center justify-between mt-2 text-xs text-gray-600">
            <span>Press Enter to send, Shift+Enter for new line</span>
            {messages.length > 0 && (
              <button
                onClick={clearChat}
                className="flex items-center gap-1 hover:text-gray-400 transition"
              >
                <RefreshCw className="w-3 h-3" />
                Clear chat
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
