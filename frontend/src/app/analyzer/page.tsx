"use client";

import { SemanticAnalyzer } from "@/components/semantic-analyzer";

export default function AnalyzerPage() {
  return (
    <div className="h-screen">
      <SemanticAnalyzer apiUrl="http://localhost:8080" />
    </div>
  );
}
