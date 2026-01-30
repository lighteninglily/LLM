"use client";

import { useState, useEffect } from "react";
import { Settings, X, Loader2, Check, Brain, MessageSquare, Network, Hash, Target, Database, BookOpen } from "lucide-react";

interface DatasetInfo {
  name: string;
  chunk_count: number;
  doc_count: number;
}

interface SQLDatabaseInfo {
  path: string;
  tables: string[];
  total_records: number;
}

interface RAGSettings {
  multi_turn_optimization: boolean;
  reasoning: boolean;
  use_knowledge_graph: boolean;
  top_n: number;
  similarity_threshold: number;
  rerank_model: string;
  chat_name: string;
  dataset_count: number;
  rag_datasets: DatasetInfo[];
  sql_database: SQLDatabaseInfo;
}

interface RAGSettingsProps {
  apiUrl?: string;
  isOpen: boolean;
  onClose: () => void;
}

export function RAGSettingsPanel({ apiUrl = "http://localhost:8080", isOpen, onClose }: RAGSettingsProps) {
  const [settings, setSettings] = useState<RAGSettings | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchSettings();
    }
  }, [isOpen]);

  const fetchSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${apiUrl}/api/settings/rag`);
      if (!resp.ok) throw new Error("Failed to fetch settings");
      const data = await resp.json();
      setSettings(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const updateSetting = async (key: string, value: boolean | number | string) => {
    if (!settings) return;
    
    setSaving(true);
    try {
      const resp = await fetch(`${apiUrl}/api/settings/rag`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ [key]: value }),
      });
      if (!resp.ok) throw new Error("Failed to update setting");
      const data = await resp.json();
      setSettings(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-[#1a1a1a] rounded-xl border border-gray-700 w-full max-w-md mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-blue-400" />
            <span className="font-semibold text-white">RAG Settings</span>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-blue-400" />
            </div>
          ) : error ? (
            <div className="text-red-400 text-center py-4">{error}</div>
          ) : settings ? (
            <div className="space-y-4">
              {/* Connected Data Sources */}
              <div className="space-y-2">
                {/* SQL Database */}
                <div className="bg-green-900/20 border border-green-800/50 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Database className="w-4 h-4 text-green-400" />
                    <span className="text-green-400 text-sm font-medium">SQL Database</span>
                  </div>
                  <p className="text-white text-sm">{settings.sql_database.total_records.toLocaleString()} records</p>
                  <p className="text-gray-500 text-xs mt-1">
                    Tables: {settings.sql_database.tables.join(", ")}
                  </p>
                </div>

                {/* RAG Datasets */}
                <div className="bg-purple-900/20 border border-purple-800/50 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <BookOpen className="w-4 h-4 text-purple-400" />
                    <span className="text-purple-400 text-sm font-medium">RAG Datasets</span>
                  </div>
                  {settings.rag_datasets.length > 0 ? (
                    <div className="space-y-1">
                      {settings.rag_datasets.map((ds, i) => (
                        <div key={i} className="text-sm">
                          <span className="text-white">{ds.name}</span>
                          <span className="text-gray-500 text-xs ml-2">
                            ({ds.chunk_count.toLocaleString()} chunks, {ds.doc_count} docs)
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-sm">No datasets linked</p>
                  )}
                  <p className="text-gray-600 text-xs mt-2">Chat: {settings.chat_name}</p>
                </div>
              </div>

              {/* Toggle settings */}
              <div className="space-y-3">
                <ToggleSetting
                  icon={<MessageSquare className="w-4 h-4" />}
                  label="Multi-turn Optimization"
                  description="Refines queries using conversation context"
                  value={settings.multi_turn_optimization}
                  onChange={(v) => updateSetting("multi_turn_optimization", v)}
                  saving={saving}
                />
                
                <ToggleSetting
                  icon={<Brain className="w-4 h-4" />}
                  label="Reasoning"
                  description="Generates answers through reasoning processes"
                  value={settings.reasoning}
                  onChange={(v) => updateSetting("reasoning", v)}
                  saving={saving}
                />
                
                <ToggleSetting
                  icon={<Network className="w-4 h-4" />}
                  label="Knowledge Graph"
                  description="Uses KG for multi-hop question answering"
                  value={settings.use_knowledge_graph}
                  onChange={(v) => updateSetting("use_knowledge_graph", v)}
                  saving={saving}
                />
              </div>

              {/* Numeric settings */}
              <div className="space-y-3 pt-2 border-t border-gray-700">
                <NumberSetting
                  icon={<Hash className="w-4 h-4" />}
                  label="Top N Chunks"
                  description="Max chunks to feed to LLM"
                  value={settings.top_n}
                  min={1}
                  max={50}
                  onChange={(v) => updateSetting("top_n", v)}
                  saving={saving}
                />
                
                <NumberSetting
                  icon={<Target className="w-4 h-4" />}
                  label="Similarity Threshold"
                  description="Min similarity score (0.0 - 1.0)"
                  value={settings.similarity_threshold}
                  min={0}
                  max={1}
                  step={0.05}
                  onChange={(v) => updateSetting("similarity_threshold", v)}
                  saving={saving}
                />
              </div>

              {/* Rerank info */}
              <div className="text-xs text-gray-500 pt-2 border-t border-gray-700">
                Rerank model: {settings.rerank_model || "(disabled)"}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function ToggleSetting({
  icon,
  label,
  description,
  value,
  onChange,
  saving,
}: {
  icon: React.ReactNode;
  label: string;
  description: string;
  value: boolean;
  onChange: (value: boolean) => void;
  saving: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-start gap-3">
        <div className="text-gray-400 mt-0.5">{icon}</div>
        <div>
          <p className="text-white text-sm font-medium">{label}</p>
          <p className="text-gray-500 text-xs">{description}</p>
        </div>
      </div>
      <button
        onClick={() => onChange(!value)}
        disabled={saving}
        className={`relative w-11 h-6 rounded-full transition-colors ${
          value ? "bg-blue-600" : "bg-gray-600"
        } ${saving ? "opacity-50" : ""}`}
      >
        <div
          className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${
            value ? "left-6" : "left-1"
          }`}
        />
      </button>
    </div>
  );
}

function NumberSetting({
  icon,
  label,
  description,
  value,
  min,
  max,
  step = 1,
  onChange,
  saving,
}: {
  icon: React.ReactNode;
  label: string;
  description: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (value: number) => void;
  saving: boolean;
}) {
  const [localValue, setLocalValue] = useState(value);

  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const handleBlur = () => {
    if (localValue !== value) {
      onChange(localValue);
    }
  };

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-start gap-3">
        <div className="text-gray-400 mt-0.5">{icon}</div>
        <div>
          <p className="text-white text-sm font-medium">{label}</p>
          <p className="text-gray-500 text-xs">{description}</p>
        </div>
      </div>
      <input
        type="number"
        value={localValue}
        min={min}
        max={max}
        step={step}
        onChange={(e) => setLocalValue(parseFloat(e.target.value))}
        onBlur={handleBlur}
        disabled={saving}
        className="w-20 bg-gray-800 border border-gray-600 rounded px-2 py-1 text-white text-sm text-right focus:outline-none focus:border-blue-500"
      />
    </div>
  );
}
