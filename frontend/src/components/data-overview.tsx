"use client";

import { useState, useEffect } from "react";
import { Database, BookOpen, Table, ChevronDown, ChevronUp, Loader2 } from "lucide-react";

interface TableInfo {
  name: string;
  record_count: number;
  columns: string[];
  sample_values: Record<string, string[]>;
}

interface DatasetInfo {
  name: string;
  chunk_count: number;
  doc_count: number;
}

interface DataOverview {
  sql_tables: TableInfo[];
  sql_total_records: number;
  rag_datasets: DatasetInfo[];
  rag_total_chunks: number;
}

interface DataOverviewProps {
  apiUrl?: string;
}

export function DataOverviewPanel({ apiUrl = "http://localhost:8080" }: DataOverviewProps) {
  const [data, setData] = useState<DataOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedTables, setExpandedTables] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const resp = await fetch(`${apiUrl}/api/settings/data-overview`);
      if (resp.ok) {
        const result = await resp.json();
        setData(result);
      }
    } catch (e) {
      console.error("Failed to fetch data overview:", e);
    } finally {
      setLoading(false);
    }
  };

  const toggleTable = (name: string) => {
    setExpandedTables((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-4">
        <Loader2 className="w-5 h-5 animate-spin text-gray-500" />
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="w-full max-w-3xl mx-auto mt-8 space-y-4">
      {/* SQL Data */}
      <div className="bg-[#111] border border-gray-800 rounded-xl overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 bg-green-900/20 border-b border-gray-800">
          <Database className="w-5 h-5 text-green-400" />
          <span className="font-medium text-green-400">SQL Database</span>
          <span className="text-gray-500 text-sm ml-auto">
            {data.sql_total_records.toLocaleString()} records
          </span>
        </div>
        <div className="divide-y divide-gray-800">
          {data.sql_tables.map((table) => (
            <div key={table.name}>
              <button
                onClick={() => toggleTable(table.name)}
                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-900/50 transition text-left"
              >
                <Table className="w-4 h-4 text-gray-500" />
                <span className="text-white font-medium">{table.name}</span>
                <span className="text-gray-500 text-sm">
                  ({table.record_count.toLocaleString()} rows)
                </span>
                <div className="ml-auto text-gray-500">
                  {expandedTables.has(table.name) ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </div>
              </button>
              {expandedTables.has(table.name) && (
                <div className="px-4 pb-4 bg-gray-900/30">
                  <div className="text-xs text-gray-500 mb-2">
                    Columns: {table.columns.join(", ")}
                  </div>
                  {Object.entries(table.sample_values).length > 0 && (
                    <div className="space-y-1">
                      <p className="text-xs text-gray-400">Sample values:</p>
                      {Object.entries(table.sample_values).slice(0, 3).map(([col, values]) => (
                        <div key={col} className="text-xs">
                          <span className="text-blue-400">{col}:</span>{" "}
                          <span className="text-gray-300">
                            {values.slice(0, 3).join(", ")}
                            {values.length > 3 && "..."}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* RAG Data */}
      <div className="bg-[#111] border border-gray-800 rounded-xl overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 bg-purple-900/20 border-b border-gray-800">
          <BookOpen className="w-5 h-5 text-purple-400" />
          <span className="font-medium text-purple-400">RAG Knowledge Base</span>
          <span className="text-gray-500 text-sm ml-auto">
            {data.rag_total_chunks.toLocaleString()} chunks
          </span>
        </div>
        <div className="px-4 py-3">
          {data.rag_datasets.length > 0 ? (
            <div className="space-y-2">
              {data.rag_datasets.map((ds, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-white">{ds.name}</span>
                  <span className="text-gray-500 text-sm">
                    ({ds.chunk_count.toLocaleString()} chunks, {ds.doc_count} docs)
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No RAG datasets linked</p>
          )}
          <p className="text-xs text-gray-600 mt-3">
            Ask about company policies, procedures, and handbook content
          </p>
        </div>
      </div>

      {/* Example queries */}
      <div className="text-center text-xs text-gray-600 mt-4">
        <p>Try asking about specific machines (MMW, galv lines), dates, products, or policies</p>
      </div>
    </div>
  );
}
