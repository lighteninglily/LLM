"use client"

import Link from "next/link"
import { 
  MessageSquare, 
  Database, 
  Sparkles, 
  Upload,
  BarChart3,
  Settings,
  ArrowRight,
  Zap
} from "lucide-react"

const sections = [
  {
    title: "AI Chat Assistant",
    description: "Ask questions about your data using natural language. Combines SQL queries with document search for comprehensive answers.",
    href: "/chat",
    icon: MessageSquare,
    color: "from-purple-500 to-indigo-600",
    bgColor: "bg-purple-50",
    iconColor: "text-purple-600",
    features: ["Natural language queries", "SQL + RAG hybrid", "Real-time data access"]
  },
  {
    title: "Data Pipeline",
    description: "Import and transform CSV files into queryable databases. Upload client data and prepare it for AI analysis.",
    href: "/pipeline",
    icon: Upload,
    color: "from-blue-500 to-cyan-600",
    bgColor: "bg-blue-50",
    iconColor: "text-blue-600",
    features: ["CSV import", "Auto-schema detection", "Batch processing"]
  },
  {
    title: "Semantic Analyzer",
    description: "Analyze your database schema with AI. Generate descriptions, detect relationships, and create semantic metadata.",
    href: "/analyzer",
    icon: Sparkles,
    color: "from-amber-500 to-orange-600",
    bgColor: "bg-amber-50",
    iconColor: "text-amber-600",
    features: ["LLM-powered analysis", "Relationship detection", "Business glossary"]
  },
]

const stats = [
  { label: "Tables", value: "5", icon: Database },
  { label: "Records", value: "33.8K", icon: BarChart3 },
  { label: "Model", value: "Qwen 14B", icon: Zap },
]

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <header className="border-b border-gray-700/50 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-6 py-4 max-w-6xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl shadow-lg shadow-purple-500/20">
                <Database className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Jennmar LLM Chat Test</h1>
                <p className="text-sm text-gray-400">AI Data Query Assistant</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {stats.map((stat) => (
                <div key={stat.label} className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 rounded-lg border border-gray-700">
                  <stat.icon className="h-4 w-4 text-gray-400" />
                  <span className="text-sm font-medium text-white">{stat.value}</span>
                  <span className="text-xs text-gray-500">{stat.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </header>
      
      <main className="container mx-auto px-6 py-12 max-w-6xl">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-white mb-4">
            Welcome to <span className="bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">Jennmar LLM Chat</span>
          </h2>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto">
            Query your business data with natural language. Our AI combines structured SQL queries 
            with document search to give you comprehensive answers.
          </p>
        </div>

        {/* Main Sections Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {sections.map((section) => (
            <Link
              key={section.href}
              href={section.href}
              className="group relative bg-gray-800/50 rounded-2xl border border-gray-700/50 p-6 hover:border-gray-600 transition-all duration-300 hover:shadow-xl hover:shadow-purple-500/5"
            >
              {/* Gradient overlay on hover */}
              <div className={`absolute inset-0 bg-gradient-to-br ${section.color} opacity-0 group-hover:opacity-5 rounded-2xl transition-opacity duration-300`} />
              
              {/* Icon */}
              <div className={`inline-flex p-3 ${section.bgColor} rounded-xl mb-4`}>
                <section.icon className={`h-6 w-6 ${section.iconColor}`} />
              </div>
              
              {/* Content */}
              <h3 className="text-xl font-semibold text-white mb-2 flex items-center gap-2">
                {section.title}
                <ArrowRight className="h-4 w-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300" />
              </h3>
              <p className="text-gray-400 text-sm mb-4 leading-relaxed">
                {section.description}
              </p>
              
              {/* Features */}
              <div className="flex flex-wrap gap-2">
                {section.features.map((feature) => (
                  <span
                    key={feature}
                    className="px-2 py-1 bg-gray-700/50 text-gray-300 text-xs rounded-md"
                  >
                    {feature}
                  </span>
                ))}
              </div>
            </Link>
          ))}
        </div>

        {/* Quick Start */}
        <div className="bg-gradient-to-r from-purple-500/10 to-indigo-500/10 rounded-2xl border border-purple-500/20 p-8">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-xl font-semibold text-white mb-2">Quick Start</h3>
              <p className="text-gray-400 mb-4">Jump straight into querying your data with AI assistance.</p>
              <div className="flex gap-3">
                <Link
                  href="/chat"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-xl font-medium shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 transition-all duration-300"
                >
                  <MessageSquare className="h-5 w-5" />
                  Start Chatting
                </Link>
                <Link
                  href="/analyzer"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-gray-700 text-white rounded-xl font-medium hover:bg-gray-600 transition-all duration-300"
                >
                  <Sparkles className="h-5 w-5" />
                  Analyze Schema
                </Link>
              </div>
            </div>
            <div className="hidden md:block">
              <div className="bg-gray-800 rounded-xl p-4 font-mono text-sm">
                <p className="text-gray-500 mb-1"># Try asking:</p>
                <p className="text-green-400">"Top 5 customers by sales"</p>
                <p className="text-green-400">"Production by machine Nov 2025"</p>
                <p className="text-green-400">"What is the sick leave policy?"</p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 text-center text-gray-500 text-sm">
          <p>Jennmar • LLM Chat Test • Powered by Qwen 14B</p>
        </div>
      </main>
    </div>
  )
}
