"use client";

import { useState, useEffect } from "react";
import {
  Database,
  Table2,
  Columns3,
  Play,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Sparkles,
  BookOpen,
  Link2,
  Hash,
  Type,
  Calendar,
  AlertCircle,
  CheckCircle,
  Loader2,
  Copy,
  Check,
  Edit3,
  Save,
  X,
} from "lucide-react";

interface ColumnProfile {
  name: string;
  data_type: string;
  description: string;
  sample_values: string[];
  unique_count: number;
  null_count: number;
  total_count: number;
  null_rate: number;
  is_primary_key: boolean;
  aliases: Record<string, string>;
  business_terms: string[];
}

interface TableProfile {
  name: string;
  description: string;
  row_count: number;
  columns: Record<string, ColumnProfile>;
  business_terms: string[];
  query_examples: { question: string; sql: string }[];
  time_column: string;
  primary_key: string;
}

interface Relationship {
  from_table: string;
  from_column: string;
  to_table: string;
  to_column: string;
  confidence: number;
}

interface SemanticLayerData {
  exists: boolean;
  generated_at?: string;
  database_name?: string;
  tables?: Record<string, TableProfile>;
  relationships?: Relationship[];
  glossary?: Record<string, string>;
  mschema?: string;
}

interface AnalysisStatus {
  status: string;
  progress: number;
  message: string;
}

interface SemanticAnalyzerProps {
  apiUrl?: string;
}

export function SemanticAnalyzer({ apiUrl = "http://localhost:8080" }: SemanticAnalyzerProps) {
  const [layer, setLayer] = useState<SemanticLayerData | null>(null);
  const [status, setStatus] = useState<AnalysisStatus>({ status: "idle", progress: 0, message: "" });
  const [loading, setLoading] = useState(true);
  const [expandedTables, setExpandedTables] = useState<Set<string>>(new Set());
  const [showMSchema, setShowMSchema] = useState(false);
  const [copied, setCopied] = useState(false);
  const [useLLM, setUseLLM] = useState(true);
  const [activeTab, setActiveTab] = useState<"tables" | "relationships" | "glossary" | "mschema">("tables");

  useEffect(() => {
    fetchLayer();
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (status.status === "running" || status.status === "starting") {
      interval = setInterval(fetchStatus, 1000);
    }
    return () => clearInterval(interval);
  }, [status.status]);

  const fetchLayer = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/semantic/layer`);
      const data = await res.json();
      setLayer(data);
      if (data.tables) {
        setExpandedTables(new Set(Object.keys(data.tables).slice(0, 2)));
      }
    } catch (e) {
      console.error("Failed to fetch semantic layer:", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/semantic/status`);
      const data = await res.json();
      setStatus(data);
      if (data.status === "complete") {
        fetchLayer();
      }
    } catch (e) {
      console.error("Failed to fetch status:", e);
    }
  };

  const runAnalysis = async () => {
    try {
      setStatus({ status: "starting", progress: 0, message: "Starting..." });
      await fetch(`${apiUrl}/api/semantic/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ use_llm: useLLM }),
      });
    } catch (e) {
      console.error("Failed to start analysis:", e);
      setStatus({ status: "error", progress: 0, message: "Failed to start" });
    }
  };

  const toggleTable = (tableName: string) => {
    setExpandedTables((prev) => {
      const next = new Set(prev);
      if (next.has(tableName)) next.delete(tableName);
      else next.add(tableName);
      return next;
    });
  };

  const copyMSchema = () => {
    if (layer?.mschema) {
      navigator.clipboard.writeText(layer.mschema);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getTypeIcon = (type: string) => {
    const t = type.toUpperCase();
    if (t.includes("INT") || t.includes("REAL") || t.includes("NUMERIC")) return <Hash className="w-3 h-3" />;
    if (t.includes("DATE") || t.includes("TIME")) return <Calendar className="w-3 h-3" />;
    return <Type className="w-3 h-3" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-[#0a0a0a] text-white">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-purple-500 to-blue-600 rounded-xl">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-lg">Semantic Layer Analyzer</h1>
            <p className="text-xs text-gray-500">
              {layer?.exists
                ? `Generated: ${new Date(layer.generated_at || "").toLocaleString()}`
                : "No semantic layer generated yet"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={useLLM}
              onChange={(e) => setUseLLM(e.target.checked)}
              className="rounded"
            />
            <span className="text-gray-400">Use LLM enrichment</span>
          </label>
          <button
            onClick={runAnalysis}
            disabled={status.status === "running" || status.status === "starting"}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 rounded-lg transition font-medium"
          >
            {status.status === "running" || status.status === "starting" ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                {status.progress}%
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Analyze Data
              </>
            )}
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      {(status.status === "running" || status.status === "starting") && (
        <div className="px-6 py-2 bg-purple-900/20 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-500 transition-all duration-300"
                style={{ width: `${status.progress}%` }}
              />
            </div>
            <span className="text-sm text-gray-400">{status.message}</span>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-gray-800">
        {[
          { id: "tables", label: "Tables", icon: Table2 },
          { id: "relationships", label: "Relationships", icon: Link2 },
          { id: "glossary", label: "Glossary", icon: BookOpen },
          { id: "mschema", label: "M-Schema", icon: Database },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition border-b-2 ${
              activeTab === tab.id
                ? "border-purple-500 text-white"
                : "border-transparent text-gray-500 hover:text-gray-300"
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {!layer?.exists ? (
          <div className="flex flex-col items-center justify-center h-64 text-center">
            <Database className="w-16 h-16 text-gray-600 mb-4" />
            <h2 className="text-xl font-semibold mb-2">No Semantic Layer</h2>
            <p className="text-gray-500 mb-4">
              Click "Analyze Data" to generate semantic metadata for your database
            </p>
          </div>
        ) : (
          <>
            {/* Tables Tab */}
            {activeTab === "tables" && layer.tables && (
              <div className="space-y-4">
                {Object.entries(layer.tables).map(([tableName, table]) => (
                  <div key={tableName} className="bg-[#111] rounded-lg border border-gray-800">
                    <button
                      onClick={() => toggleTable(tableName)}
                      className="w-full flex items-center justify-between p-4 hover:bg-gray-800/50 transition"
                    >
                      <div className="flex items-center gap-3">
                        <Table2 className="w-5 h-5 text-purple-400" />
                        <div className="text-left">
                          <h3 className="font-semibold">{tableName}</h3>
                          <p className="text-sm text-gray-500">{table.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-sm text-gray-500">{table.row_count.toLocaleString()} rows</span>
                        <span className="text-sm text-gray-500">
                          {Object.keys(table.columns || {}).length} columns
                        </span>
                        {table.time_column && (
                          <span className="text-xs px-2 py-1 bg-blue-900/50 text-blue-400 rounded">
                            Has dates
                          </span>
                        )}
                        {expandedTables.has(tableName) ? (
                          <ChevronUp className="w-5 h-5 text-gray-500" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-gray-500" />
                        )}
                      </div>
                    </button>

                    {expandedTables.has(tableName) && (
                      <div className="border-t border-gray-800 p-4">
                        {/* Business Terms */}
                        {table.business_terms && table.business_terms.length > 0 && (
                          <div className="mb-4">
                            <h4 className="text-xs font-medium text-gray-500 mb-2">BUSINESS TERMS</h4>
                            <div className="flex flex-wrap gap-2">
                              {table.business_terms.map((term, i) => (
                                <span key={i} className="px-2 py-1 bg-purple-900/30 text-purple-400 text-xs rounded">
                                  {term}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Columns */}
                        <h4 className="text-xs font-medium text-gray-500 mb-2">COLUMNS</h4>
                        <div className="space-y-2">
                          {Object.entries(table.columns || {}).map(([colName, col]) => (
                            <div key={colName} className="flex items-start gap-3 p-2 bg-gray-900/50 rounded">
                              <div className="mt-1 text-gray-500">{getTypeIcon(col.data_type)}</div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className="font-mono text-sm">{colName}</span>
                                  <span className="text-xs text-gray-600">({col.data_type})</span>
                                  {col.is_primary_key && (
                                    <span className="text-xs px-1 bg-yellow-900/50 text-yellow-500 rounded">PK</span>
                                  )}
                                </div>
                                {col.description && (
                                  <p className="text-xs text-gray-500 mt-1">{col.description}</p>
                                )}
                                {col.sample_values && col.sample_values.length > 0 && (
                                  <div className="mt-1">
                                    <span className="text-xs text-gray-600">Samples: </span>
                                    <span className="text-xs text-gray-400">
                                      {col.sample_values.slice(0, 5).join(", ")}
                                    </span>
                                  </div>
                                )}
                                {col.aliases && Object.keys(col.aliases).length > 0 && (
                                  <div className="mt-1 flex flex-wrap gap-1">
                                    {Object.entries(col.aliases).map(([alias, value]) => (
                                      <span key={alias} className="text-xs px-1 bg-green-900/30 text-green-400 rounded">
                                        {alias} → {value}
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>
                              <div className="text-right text-xs text-gray-600">
                                <div>{col.unique_count} unique</div>
                                <div>{(col.null_rate * 100).toFixed(1)}% null</div>
                              </div>
                            </div>
                          ))}
                        </div>

                        {/* Query Examples */}
                        {table.query_examples && table.query_examples.length > 0 && (
                          <div className="mt-4">
                            <h4 className="text-xs font-medium text-gray-500 mb-2">EXAMPLE QUERIES</h4>
                            <div className="space-y-2">
                              {table.query_examples.slice(0, 3).map((ex, i) => (
                                <div key={i} className="p-2 bg-gray-900/50 rounded">
                                  <p className="text-sm text-gray-300">{ex.question}</p>
                                  <pre className="mt-1 text-xs text-green-400 overflow-x-auto">{ex.sql}</pre>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Relationships Tab */}
            {activeTab === "relationships" && (
              <div className="space-y-2">
                {layer.relationships && layer.relationships.length > 0 ? (
                  layer.relationships.map((rel, i) => (
                    <div key={i} className="flex items-center gap-3 p-3 bg-[#111] rounded-lg border border-gray-800">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm text-purple-400">{rel.from_table}</span>
                        <span className="text-gray-600">.</span>
                        <span className="font-mono text-sm">{rel.from_column}</span>
                      </div>
                      <Link2 className="w-4 h-4 text-gray-500" />
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm text-blue-400">{rel.to_table}</span>
                        <span className="text-gray-600">.</span>
                        <span className="font-mono text-sm">{rel.to_column}</span>
                      </div>
                      {rel.confidence && (
                        <span className="ml-auto text-xs text-gray-500">
                          {(rel.confidence * 100).toFixed(0)}% confidence
                        </span>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500">No relationships detected</p>
                )}
              </div>
            )}

            {/* Glossary Tab */}
            {activeTab === "glossary" && (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {layer.glossary &&
                  Object.entries(layer.glossary).map(([term, definition]) => (
                    <div key={term} className="p-3 bg-[#111] rounded-lg border border-gray-800">
                      <span className="font-mono text-sm text-yellow-400">{term}</span>
                      <p className="text-sm text-gray-400 mt-1">{definition}</p>
                    </div>
                  ))}
              </div>
            )}

            {/* M-Schema Tab */}
            {activeTab === "mschema" && (
              <div className="relative">
                <div className="absolute top-2 right-2">
                  <button
                    onClick={copyMSchema}
                    className="flex items-center gap-1 px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded text-sm"
                  >
                    {copied ? (
                      <>
                        <Check className="w-4 h-4 text-green-400" /> Copied
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" /> Copy
                      </>
                    )}
                  </button>
                </div>
                <pre className="p-4 bg-[#111] rounded-lg border border-gray-800 text-sm text-gray-300 overflow-x-auto whitespace-pre-wrap">
                  {layer.mschema}
                </pre>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
