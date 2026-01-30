"use client";

import { useState, useEffect, useRef } from "react";
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
  Settings,
  Trash2,
  Plus,
  MessageSquare,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Package,
  Users,
  Calendar,
  Search,
  Zap,
  Target,
  FileText,
  HelpCircle,
  DollarSign,
  Hash,
  Download,
  ArrowUpRight,
  ArrowDownRight,
  Upload,
  X,
  Table,
  FileSpreadsheet,
} from "lucide-react";
import { RAGSettingsPanel } from "./rag-settings";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  source?: "sql" | "rag";
  sqlQuery?: string;
  data?: any[];
  rowCount?: number;
  timestamp: Date;
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
}

interface TestPrompt {
  category: string;
  icon: any;
  color: string;
  prompts: { text: string; description: string }[];
}

const TEST_PROMPTS: TestPrompt[] = [
  {
    category: "PRODUCTION Table",
    icon: BarChart3,
    color: "text-green-400",
    prompts: [
      { text: "Top 5 machines by production", description: "5,576 rows • Apr 2025 - Feb 2027" },
      { text: "What did DRAWING_GZ1 machine produce?", description: "Machine breakdown" },
      { text: "Show production for November 2025", description: "Time series data" },
    ],
  },
  {
    category: "SALES Table",
    icon: TrendingUp,
    color: "text-blue-400",
    prompts: [
      { text: "Top 10 customers by sales amount", description: "24,908 rows • Sep-Oct 2025" },
      { text: "Sales breakdown by state in September 2025", description: "Geographic analysis" },
      { text: "What products sold most in October 2025?", description: "Product performance" },
    ],
  },
  {
    category: "INVENTORY Table",
    icon: Package,
    color: "text-orange-400",
    prompts: [
      { text: "Show inventory in warehouse M1", description: "2,246 rows • warehouses M1-M7" },
      { text: "Find products containing mesh in inventory", description: "Partial text search" },
      { text: "What products have Friction in inventory?", description: "Product search" },
    ],
  },
  {
    category: "OPEN_ORDERS Table",
    icon: FileText,
    color: "text-purple-400",
    prompts: [
      { text: "Show all open customer orders", description: "246 rows • customer orders" },
      { text: "Orders with largest outstanding quantities", description: "Volume analysis" },
      { text: "Which customers have orders due soon?", description: "Due date analysis" },
    ],
  },
  {
    category: "PURCHASE_ORDERS Table",
    icon: FileText,
    color: "text-cyan-400",
    prompts: [
      { text: "Show all outstanding purchase orders", description: "896 rows • supplier POs" },
      { text: "Which vendors have the most open POs?", description: "Vendor analysis" },
      { text: "What parts are we waiting to receive?", description: "Incoming materials" },
    ],
  },
  {
    category: "RAG Knowledge Base",
    icon: BookOpen,
    color: "text-pink-400",
    prompts: [
      { text: "What is the sick leave policy?", description: "901 chunks • HR handbook" },
      { text: "Explain the whistleblower policy", description: "Reporting procedures" },
      { text: "What is the disciplinary process?", description: "HR procedures" },
    ],
  },
  {
    category: "Advanced Analysis",
    icon: Zap,
    color: "text-yellow-400",
    prompts: [
      { text: "What are the top selling products?", description: "Sales ranking" },
      { text: "Which vendors have outstanding purchase orders?", description: "Vendor analysis" },
      { text: "Summarize sales performance in September 2025", description: "Executive summary" },
      { text: "Show me a complete overview of the M1 warehouse", description: "Comprehensive view" },
    ],
  },
];

interface ChatWorkspaceProps {
  apiUrl?: string;
}

// KPI Card Component for single-value displays
const KPICard = ({ value, label, icon: Icon, trend, subtext }: {
  value: string;
  label: string;
  icon?: any;
  trend?: 'up' | 'down' | null;
  subtext?: string;
}) => (
  <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 border border-gray-700 shadow-lg">
    <div className="flex items-center justify-between mb-2">
      <span className="text-gray-400 text-sm font-medium">{label}</span>
      {Icon && <Icon className="w-5 h-5 text-gray-500" />}
    </div>
    <div className="flex items-end gap-3">
      <span className="text-3xl font-bold text-white">{value}</span>
      {trend && (
        <span className={`flex items-center text-sm ${trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
          {trend === 'up' ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
        </span>
      )}
    </div>
    {subtext && <p className="text-gray-500 text-xs mt-2">{subtext}</p>}
  </div>
);

// Summary Stats Bar Component
const SummaryStats = ({ stats }: { stats: { label: string; value: string; icon?: any }[] }) => (
  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
    {stats.map((stat, i) => (
      <div key={i} className="bg-gray-800/50 rounded-lg px-4 py-3 border border-gray-700/50">
        <div className="text-gray-500 text-xs mb-1">{stat.label}</div>
        <div className="text-white font-semibold text-lg">{stat.value}</div>
      </div>
    ))}
  </div>
);

// Helper to detect if content is a single KPI value
const detectKPIContent = (content: string): { isKPI: boolean; value?: string; label?: string; isCurrency?: boolean } => {
  // Match patterns like "Total: $1,234,567" or "Count: 5,432"
  const kpiPattern = /^(?:the\s+)?(?:total|sum|count|average|maximum|minimum|overall)[\s:]+(?:is\s+)?(\$?[\d,]+\.?\d*)/i;
  const match = content.match(kpiPattern);
  if (match) {
    return { isKPI: true, value: match[1], label: content.split(/[:]/)[0], isCurrency: match[1].includes('$') };
  }
  // Single line with just a big number
  if (/^\$?[\d,]+\.?\d*$/.test(content.trim())) {
    return { isKPI: true, value: content.trim(), isCurrency: content.includes('$') };
  }
  return { isKPI: false };
};

// Helper to extract summary stats from table data
const extractTableStats = (content: string): { label: string; value: string }[] | null => {
  const lines = content.split('\n').filter(l => l.includes('|'));
  if (lines.length < 3) return null;
  
  // Find numeric columns
  const dataRows = lines.slice(2); // Skip header and separator
  const values: number[] = [];
  
  dataRows.forEach(row => {
    const cells = row.split('|').filter(c => c.trim());
    cells.forEach(cell => {
      const num = cell.replace(/[\$,]/g, '').trim();
      if (/^-?\d+\.?\d*$/.test(num)) {
        values.push(parseFloat(num));
      }
    });
  });
  
  if (values.length === 0) return null;
  
  const sum = values.reduce((a, b) => a + b, 0);
  const avg = sum / values.length;
  const max = Math.max(...values);
  
  // Check if values look like currency (large numbers)
  const isCurrency = sum > 1000;
  const format = (n: number) => isCurrency ? `$${n.toLocaleString(undefined, {maximumFractionDigits: 0})}` : n.toLocaleString(undefined, {maximumFractionDigits: 1});
  
  return [
    { label: 'Total', value: format(sum) },
    { label: 'Average', value: format(avg) },
    { label: 'Highest', value: format(max) },
    { label: 'Count', value: dataRows.length.toString() },
  ];
};

// Export to CSV helper
const exportToCSV = (content: string, filename: string = 'data.csv') => {
  const lines = content.split('\n').filter(l => l.includes('|'));
  if (lines.length < 2) return;
  
  const csvRows: string[] = [];
  lines.forEach((line, i) => {
    if (i === 1) return; // Skip separator line
    const cells = line.split('|').filter(c => c.trim()).map(c => `"${c.trim().replace(/"/g, '""')}"`);
    csvRows.push(cells.join(','));
  });
  
  const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
};

// Upload state interface
interface UploadedTable {
  table_name: string;
  filename: string;
  columns: string[];
  row_count: number;
}

export function ChatWorkspace({ apiUrl = "http://localhost:8080" }: ChatWorkspaceProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedSql, setExpandedSql] = useState<Set<string>>(new Set());
  const [showSettings, setShowSettings] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(["PRODUCTION Table", "SALES Table", "INVENTORY Table", "OPEN_ORDERS Table", "PURCHASE_ORDERS Table", "RAG Knowledge Base"]));
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadedTables, setUploadedTables] = useState<UploadedTable[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadPreview, setUploadPreview] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const activeConversation = conversations.find((c) => c.id === activeConversationId);
  const messages = activeConversation?.messages || [];

  useEffect(() => {
    // Create initial conversation
    if (conversations.length === 0) {
      createNewConversation();
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const createNewConversation = () => {
    const newConv: Conversation = {
      id: Date.now().toString(),
      title: "New Chat",
      messages: [],
      createdAt: new Date(),
    };
    setConversations((prev) => [newConv, ...prev]);
    setActiveConversationId(newConv.id);
  };

  const deleteConversation = (id: string) => {
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (activeConversationId === id) {
      const remaining = conversations.filter((c) => c.id !== id);
      if (remaining.length > 0) {
        setActiveConversationId(remaining[0].id);
      } else {
        createNewConversation();
      }
    }
  };

  // File upload handlers
  const handleFileUpload = async (file: File) => {
    setIsUploading(true);
    setUploadPreview(null);
    
    const formData = new FormData();
    formData.append('file', file);
    
    const endpoint = file.name.toLowerCase().endsWith('.csv') 
      ? `${apiUrl}/api/upload/csv`
      : `${apiUrl}/api/upload/excel`;
    
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }
      
      const result = await response.json();
      setUploadPreview(result);
      setUploadedTables(prev => [...prev, {
        table_name: result.table_name,
        filename: file.name,
        columns: result.columns,
        row_count: result.row_count,
      }]);
      
    } catch (error: any) {
      alert(`Upload failed: ${error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && (file.name.endsWith('.csv') || file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
      handleFileUpload(file);
    }
  };

  const deleteUploadedTable = async (tableName: string) => {
    try {
      await fetch(`${apiUrl}/api/upload/tables/${tableName}`, { method: 'DELETE' });
      setUploadedTables(prev => prev.filter(t => t.table_name !== tableName));
    } catch (error) {
      console.error('Failed to delete table:', error);
    }
  };

  const handleSubmit = async (e?: React.FormEvent, promptText?: string) => {
    e?.preventDefault();
    const question = promptText || input.trim();
    if (!question || isLoading || !activeConversationId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: question,
      timestamp: new Date(),
    };

    // Update conversation with user message and title
    setConversations((prev) =>
      prev.map((c) =>
        c.id === activeConversationId
          ? {
              ...c,
              messages: [...c.messages, userMessage],
              title: c.messages.length === 0 ? question.slice(0, 40) + (question.length > 40 ? "..." : "") : c.title,
            }
          : c
      )
    );

    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch(`${apiUrl}/api/hybrid/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
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
        timestamp: new Date(),
      };

      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeConversationId ? { ...c, messages: [...c.messages, assistantMessage] } : c
        )
      );
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, there was an error processing your request.",
        timestamp: new Date(),
      };
      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeConversationId ? { ...c, messages: [...c.messages, errorMessage] } : c
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleSqlExpanded = (id: string) => {
    setExpandedSql((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleCategory = (category: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) next.delete(category);
      else next.add(category);
      return next;
    });
  };

  return (
    <div className="flex h-screen bg-[#0a0a0a] text-white">
      {/* Settings Panel */}
      <RAGSettingsPanel apiUrl={apiUrl} isOpen={showSettings} onClose={() => setShowSettings(false)} />

      {/* Left Sidebar - Chat History */}
      <div className="w-64 bg-[#111] border-r border-gray-800 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-800">
          <button
            onClick={createNewConversation}
            className="w-full flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition font-medium"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </button>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={`group flex items-center gap-2 px-4 py-3 cursor-pointer hover:bg-gray-800/50 border-l-2 transition ${
                conv.id === activeConversationId ? "bg-gray-800/50 border-blue-500" : "border-transparent"
              }`}
              onClick={() => setActiveConversationId(conv.id)}
            >
              <MessageSquare className="w-4 h-4 text-gray-500 flex-shrink-0" />
              <span className="flex-1 text-sm truncate text-gray-300">{conv.title}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteConversation(conv.id);
                }}
                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-700 rounded transition"
              >
                <Trash2 className="w-3 h-3 text-gray-500" />
              </button>
            </div>
          ))}
        </div>

        {/* Uploaded Tables */}
        {uploadedTables.length > 0 && (
          <div className="p-3 border-t border-gray-800">
            <div className="text-xs font-medium text-gray-500 mb-2">UPLOADED DATA</div>
            {uploadedTables.map((table) => (
              <div key={table.table_name} className="flex items-center justify-between p-2 bg-gray-800/50 rounded mb-1 text-xs">
                <div className="flex items-center gap-2 truncate">
                  <FileSpreadsheet className="w-3 h-3 text-green-400" />
                  <span className="truncate">{table.filename}</span>
                </div>
                <button onClick={() => deleteUploadedTable(table.table_name)} className="text-gray-500 hover:text-red-400">
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Bottom Buttons */}
        <div className="p-4 border-t border-gray-800 space-y-2">
          <button
            onClick={() => setShowUploadModal(true)}
            className="w-full flex items-center gap-2 px-4 py-2 text-gray-400 hover:text-white hover:bg-green-900/30 rounded-lg transition"
          >
            <Upload className="w-4 h-4 text-green-400" />
            Upload CSV/Excel
          </button>
          <a
            href="/analyzer"
            className="w-full flex items-center gap-2 px-4 py-2 text-gray-400 hover:text-white hover:bg-purple-900/30 rounded-lg transition"
          >
            <Sparkles className="w-4 h-4 text-purple-400" />
            Semantic Analyzer
          </a>
          <button
            onClick={() => setShowSettings(true)}
            className="w-full flex items-center gap-2 px-4 py-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition"
          >
            <Settings className="w-4 h-4" />
            RAG Settings
          </button>
        </div>
      </div>

      {/* Center - Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-lg">ASW Hybrid Query Assistant</h1>
              <p className="text-xs text-gray-500">SQL Database + RAG Knowledge Base</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Database className="w-4 h-4 text-green-500" />
            <span>33,872 records</span>
            <span className="mx-2">•</span>
            <BookOpen className="w-4 h-4 text-purple-500" />
            <span>901 chunks</span>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full px-8 py-12 text-center">
              <div className="p-4 bg-gradient-to-br from-blue-500/20 to-purple-600/20 rounded-2xl mb-6">
                <Sparkles className="w-12 h-12 text-blue-400" />
              </div>
              <h2 className="text-2xl font-bold mb-2">Ready to Query</h2>
              <p className="text-gray-500 mb-6 max-w-md">
                Ask questions about production, sales, inventory, orders, or company policies.
                Select a test prompt from the right panel to get started.
              </p>
              <div className="flex gap-4 text-sm">
                <div className="flex items-center gap-2 px-3 py-2 bg-green-900/30 rounded-lg">
                  <Database className="w-4 h-4 text-green-400" />
                  <span className="text-green-400">SQL: Structured Data</span>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 bg-purple-900/30 rounded-lg">
                  <BookOpen className="w-4 h-4 text-purple-400" />
                  <span className="text-purple-400">RAG: Handbook & Policies</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto py-6">
              {messages.map((message) => (
                <div key={message.id} className="group px-6 py-4 hover:bg-[#111]/50">
                  <div className="flex gap-4">
                    {/* Avatar */}
                    <div className="flex-shrink-0">
                      {message.role === "user" ? (
                        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                          <User className="w-4 h-4" />
                        </div>
                      ) : (
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-blue-500 flex items-center justify-center">
                          <Bot className="w-4 h-4" />
                        </div>
                      )}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-sm">
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
                            {message.source === "sql" ? "SQL" : "RAG"}
                          </span>
                        )}
                        {message.rowCount !== undefined && (
                          <span className="text-xs text-gray-500">{message.rowCount} rows</span>
                        )}
                      </div>

                      {/* Message content */}
                      <div className="prose prose-invert prose-sm max-w-none">
                        {/* Check for KPI-style single value */}
                        {(() => {
                          const kpi = detectKPIContent(message.content);
                          if (kpi.isKPI && kpi.value) {
                            return (
                              <KPICard 
                                value={kpi.value} 
                                label={kpi.label || "Result"} 
                                icon={kpi.isCurrency ? DollarSign : Hash}
                              />
                            );
                          }
                          
                          // Check for table content and show summary stats
                          const hasTable = message.content.includes('|') && message.content.includes('---');
                          const stats = hasTable ? extractTableStats(message.content) : null;
                          
                          return (
                            <>
                              {/* Summary stats above table */}
                              {stats && <SummaryStats stats={stats} />}
                              
                              {/* Main content */}
                              <ReactMarkdown 
                                remarkPlugins={[remarkGfm]}
                                components={{
                                  table: ({ children }) => (
                                    <div className="overflow-x-auto my-4 rounded-lg border border-gray-700">
                                      <table className="w-full text-sm">{children}</table>
                                    </div>
                                  ),
                                  thead: ({ children }) => (
                                    <thead className="bg-gray-800 text-gray-200">{children}</thead>
                                  ),
                                  th: ({ children }) => (
                                    <th className="px-4 py-3 text-left font-semibold border-b border-gray-700 whitespace-nowrap">{children}</th>
                                  ),
                                  td: ({ children }) => {
                                    const content = String(children);
                                    const isNumeric = /^[\$\-]?[\d,]+\.?\d*%?$/.test(content.trim());
                                    const isCurrency = content.includes('$');
                                    return (
                                      <td className={`px-4 py-2.5 border-b border-gray-800/50 ${isNumeric ? 'text-right font-mono' : ''} ${isCurrency ? 'text-green-400' : ''}`}>
                                        {children}
                                      </td>
                                    );
                                  },
                                  tr: ({ children, ...props }) => (
                                    <tr className="hover:bg-gray-800/50 transition-colors even:bg-gray-900/40">{children}</tr>
                                  ),
                                }}
                              >
                                {message.content}
                              </ReactMarkdown>
                              
                              {/* Export button for tables */}
                              {hasTable && (
                                <button
                                  onClick={() => exportToCSV(message.content, `data-${message.id}.csv`)}
                                  className="mt-2 flex items-center gap-2 text-xs text-gray-500 hover:text-blue-400 transition-colors"
                                >
                                  <Download className="w-3 h-3" />
                                  Export CSV
                                </button>
                              )}
                            </>
                          );
                        })()}
                      </div>

                      {/* SQL Query expandable */}
                      {message.sqlQuery && (
                        <div className="mt-3">
                          <button
                            onClick={() => toggleSqlExpanded(message.id)}
                            className="flex items-center gap-2 text-xs text-gray-500 hover:text-gray-300"
                          >
                            {expandedSql.has(message.id) ? (
                              <ChevronUp className="w-3 h-3" />
                            ) : (
                              <ChevronDown className="w-3 h-3" />
                            )}
                            View SQL Query
                          </button>
                          {expandedSql.has(message.id) && (
                            <pre className="mt-2 p-3 bg-gray-900 rounded-lg text-xs overflow-x-auto text-green-400">
                              {message.sqlQuery}
                            </pre>
                          )}
                        </div>
                      )}

                      {/* Copy button */}
                      {message.role === "assistant" && (
                        <button
                          onClick={() => copyToClipboard(message.content, message.id)}
                          className="mt-2 flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300"
                        >
                          {copiedId === message.id ? (
                            <>
                              <Check className="w-3 h-3" /> Copied
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" /> Copy
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="px-6 py-4 flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-blue-500 flex items-center justify-center animate-pulse">
                    <Loader2 className="w-4 h-4 animate-spin" />
                  </div>
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400 text-sm">Analyzing your query...</span>
                    </div>
                    <div className="space-y-2">
                      <div className="h-4 bg-gray-800 rounded animate-pulse w-3/4"></div>
                      <div className="h-4 bg-gray-800 rounded animate-pulse w-1/2"></div>
                      <div className="h-4 bg-gray-800 rounded animate-pulse w-5/6"></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-800">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            <div className="relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit();
                  }
                }}
                placeholder="Ask about production, sales, inventory, or company policies..."
                className="w-full bg-[#1a1a1a] border border-gray-700 rounded-xl px-4 py-3 pr-12 resize-none focus:outline-none focus:border-blue-500 text-sm"
                rows={1}
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg transition"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Right Sidebar - Test Prompts */}
      <div className="w-80 bg-[#111] border-l border-gray-800 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <h2 className="font-semibold flex items-center gap-2">
            <Target className="w-4 h-4 text-blue-400" />
            Test Prompts
          </h2>
          <p className="text-xs text-gray-500 mt-1">Click any prompt to test</p>
        </div>

        <div className="flex-1 overflow-y-auto">
          {TEST_PROMPTS.map((category) => (
            <div key={category.category} className="border-b border-gray-800">
              <button
                onClick={() => toggleCategory(category.category)}
                className="w-full flex items-center gap-2 px-4 py-3 hover:bg-gray-800/50 transition"
              >
                <category.icon className={`w-4 h-4 ${category.color}`} />
                <span className="flex-1 text-left text-sm font-medium">{category.category}</span>
                {expandedCategories.has(category.category) ? (
                  <ChevronUp className="w-4 h-4 text-gray-500" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-500" />
                )}
              </button>
              {expandedCategories.has(category.category) && (
                <div className="pb-2">
                  {category.prompts.map((prompt, i) => (
                    <button
                      key={i}
                      onClick={() => handleSubmit(undefined, prompt.text)}
                      disabled={isLoading}
                      className="w-full text-left px-4 py-2 hover:bg-gray-800/50 transition group"
                    >
                      <p className="text-sm text-gray-300 group-hover:text-white">{prompt.text}</p>
                      <p className="text-xs text-gray-600">{prompt.description}</p>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Quick Stats */}
        <div className="p-4 border-t border-gray-800 bg-gray-900/50">
          <h3 className="text-xs font-medium text-gray-500 mb-2">DATA SOURCES</h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-gray-400">Production</span>
                <p className="text-gray-600 text-[10px]">Apr 2025 - Feb 2027</p>
              </div>
              <span className="text-green-400">5,576 rows</span>
            </div>
            <div className="flex justify-between items-start">
              <div>
                <span className="text-gray-400">Sales</span>
                <p className="text-gray-600 text-[10px]">Sep - Oct 2025</p>
              </div>
              <span className="text-blue-400">24,908 rows</span>
            </div>
            <div className="flex justify-between items-start">
              <div>
                <span className="text-gray-400">Inventory</span>
                <p className="text-gray-600 text-[10px]">M1-M7 warehouses</p>
              </div>
              <span className="text-orange-400">2,246 rows</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Orders</span>
              <span className="text-purple-400">1,142 rows</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Handbook</span>
              <span className="text-pink-400">901 chunks</span>
            </div>
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-gray-900 rounded-xl border border-gray-700 w-full max-w-lg mx-4">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Upload className="w-5 h-5 text-green-400" />
                Upload Data File
              </h2>
              <button onClick={() => { setShowUploadModal(false); setUploadPreview(null); }} className="text-gray-500 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6">
              {!uploadPreview ? (
                <>
                  {/* Drop Zone */}
                  <div
                    onDrop={handleDrop}
                    onDragOver={(e) => e.preventDefault()}
                    className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center hover:border-green-500 transition-colors cursor-pointer"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                    {isUploading ? (
                      <div className="flex flex-col items-center gap-3">
                        <Loader2 className="w-10 h-10 text-green-400 animate-spin" />
                        <p className="text-gray-400">Uploading and processing...</p>
                      </div>
                    ) : (
                      <>
                        <FileSpreadsheet className="w-12 h-12 text-gray-500 mx-auto mb-4" />
                        <p className="text-gray-300 mb-2">Drop CSV or Excel file here</p>
                        <p className="text-gray-500 text-sm">or click to browse</p>
                        <p className="text-gray-600 text-xs mt-4">Supports .csv, .xlsx, .xls</p>
                      </>
                    )}
                  </div>

                  {/* Info */}
                  <div className="mt-4 p-3 bg-gray-800/50 rounded-lg text-xs text-gray-400">
                    <p className="font-medium text-gray-300 mb-1">Session-only storage</p>
                    <p>Your uploaded data will be available for queries during this session. It will be removed when you close the browser.</p>
                  </div>
                </>
              ) : (
                <>
                  {/* Upload Success */}
                  <div className="text-center mb-4">
                    <div className="w-12 h-12 bg-green-900/50 rounded-full flex items-center justify-center mx-auto mb-3">
                      <Check className="w-6 h-6 text-green-400" />
                    </div>
                    <h3 className="font-semibold text-green-400">Upload Successful!</h3>
                    <p className="text-gray-400 text-sm mt-1">Table: <code className="text-blue-400">{uploadPreview.table_name}</code></p>
                    <p className="text-gray-500 text-xs">{uploadPreview.row_count} rows • {uploadPreview.columns.length} columns</p>
                  </div>

                  {/* Preview Table */}
                  <div className="border border-gray-700 rounded-lg overflow-hidden">
                    <div className="bg-gray-800 px-3 py-2 text-xs font-medium text-gray-400">Preview (first 5 rows)</div>
                    <div className="overflow-x-auto max-h-48">
                      <table className="w-full text-xs">
                        <thead className="bg-gray-800/50">
                          <tr>
                            {uploadPreview.columns.map((col: string) => (
                              <th key={col} className="px-3 py-2 text-left text-gray-400 font-medium whitespace-nowrap">{col}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {uploadPreview.preview.map((row: any, i: number) => (
                            <tr key={i} className="border-t border-gray-800">
                              {uploadPreview.columns.map((col: string) => (
                                <td key={col} className="px-3 py-2 text-gray-300 whitespace-nowrap">{String(row[col] ?? '-').slice(0, 30)}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Example Queries */}
                  <div className="mt-4 p-3 bg-blue-900/20 rounded-lg border border-blue-800/50">
                    <p className="text-xs font-medium text-blue-400 mb-2">Try these queries:</p>
                    <ul className="text-xs text-gray-400 space-y-1">
                      <li>• "Show me all data from {uploadPreview.table_name}"</li>
                      <li>• "Summarize the uploaded file"</li>
                      <li>• "Compare uploaded data with sales"</li>
                    </ul>
                  </div>
                </>
              )}
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-3 p-4 border-t border-gray-700">
              {uploadPreview ? (
                <>
                  <button
                    onClick={() => setUploadPreview(null)}
                    className="px-4 py-2 text-gray-400 hover:text-white transition"
                  >
                    Upload Another
                  </button>
                  <button
                    onClick={() => { setShowUploadModal(false); setUploadPreview(null); }}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition"
                  >
                    Done
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 text-gray-400 hover:text-white transition"
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
