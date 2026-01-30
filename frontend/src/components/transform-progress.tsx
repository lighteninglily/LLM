"use client"

import { useEffect, useState } from "react"
import { 
  CheckCircle, XCircle, Loader2, Clock, FileText, 
  Database, Sparkles, Upload, ChevronDown, ChevronUp 
} from "lucide-react"

interface FileProgress {
  name: string
  status: "pending" | "analyzing" | "transforming" | "completed" | "failed"
  progress: number
  records?: number
  batches_total?: number
  batches_done?: number
  meta_tags?: string[]
}

interface TransformProgressProps {
  jobId: string
  files: string[]
  status: "pending" | "running" | "completed" | "failed" | "cancelled"
  logs: string[]
  onClose?: () => void
}

export function TransformProgress({ 
  jobId, 
  files, 
  status, 
  logs,
  onClose 
}: TransformProgressProps) {
  const [fileProgress, setFileProgress] = useState<FileProgress[]>([])
  const [showLogs, setShowLogs] = useState(false)
  const [currentStage, setCurrentStage] = useState<string>("Initializing...")

  useEffect(() => {
    // Initialize file progress from file list
    setFileProgress(files.map(f => ({
      name: f.split('/').pop() || f,
      status: "pending",
      progress: 0
    })))
  }, [files])

  useEffect(() => {
    // Parse logs to update file progress
    logs.forEach(log => {
      if (log.includes("Analyzing file schema")) {
        const match = log.match(/Analyzing.*?(\w+\.csv)/i)
        if (match) {
          updateFileStatus(match[1], "analyzing", 10)
          setCurrentStage(`Analyzing ${match[1]}...`)
        }
      } else if (log.includes("File analysis:")) {
        const match = log.match(/(\w+\.csv).*?(\d+) entities/i)
        if (match) {
          updateFileStatus(match[1], "analyzing", 30)
        }
      } else if (log.includes("Transforming")) {
        const match = log.match(/Transforming (.*?\.csv): (\d+) records in (\d+) batches/i)
        if (match) {
          updateFileStatus(match[1], "transforming", 40, {
            records: parseInt(match[2]),
            batches_total: parseInt(match[3]),
            batches_done: 0
          })
          setCurrentStage(`Transforming ${match[1]}...`)
        }
      } else if (log.includes("Wrote") && log.includes("paragraphs")) {
        const match = log.match(/Wrote (\d+) paragraphs to (.*?)\.txt/i)
        if (match) {
          const csvName = match[2] + ".csv"
          updateFileStatus(csvName, "completed", 100)
        }
      }
    })
  }, [logs])

  function updateFileStatus(
    fileName: string, 
    newStatus: FileProgress["status"], 
    progress: number,
    extra?: Partial<FileProgress>
  ) {
    setFileProgress(prev => prev.map(f => 
      f.name.includes(fileName.replace('.csv', '')) 
        ? { ...f, status: newStatus, progress, ...extra }
        : f
    ))
  }

  const completedCount = fileProgress.filter(f => f.status === "completed").length
  const totalCount = fileProgress.length
  const overallProgress = totalCount > 0 
    ? Math.round((completedCount / totalCount) * 100)
    : 0

  const stages = [
    { id: "init", label: "Initialize", icon: Clock },
    { id: "analyze", label: "Analyze Schema", icon: Sparkles },
    { id: "transform", label: "Transform", icon: FileText },
    { id: "complete", label: "Complete", icon: CheckCircle },
  ]

  const currentStageIndex = status === "completed" ? 3 
    : status === "running" ? (currentStage.includes("Analyzing") ? 1 : 2)
    : 0

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-blue-600 to-blue-700">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white">Transformation Progress</h2>
              <p className="text-blue-100 text-sm mt-1">Job ID: {jobId}</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-white">{overallProgress}%</div>
              <div className="text-blue-100 text-sm">{completedCount}/{totalCount} files</div>
            </div>
          </div>

          {/* Overall progress bar */}
          <div className="mt-4 h-2 bg-blue-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-white transition-all duration-500"
              style={{ width: `${overallProgress}%` }}
            />
          </div>
        </div>

        {/* Stage indicators */}
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <div className="flex items-center justify-between">
            {stages.map((stage, i) => {
              const Icon = stage.icon
              const isActive = i === currentStageIndex
              const isComplete = i < currentStageIndex
              return (
                <div key={stage.id} className="flex items-center">
                  <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                    isComplete ? "bg-green-100 text-green-700" :
                    isActive ? "bg-blue-100 text-blue-700" :
                    "bg-gray-100 text-gray-400"
                  }`}>
                    {isComplete ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : isActive ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Icon className="h-4 w-4" />
                    )}
                    {stage.label}
                  </div>
                  {i < stages.length - 1 && (
                    <div className={`w-8 h-0.5 mx-2 ${
                      i < currentStageIndex ? "bg-green-300" : "bg-gray-200"
                    }`} />
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* File list */}
        <div className="flex-1 overflow-y-auto p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-3">Files</h3>
          <div className="space-y-2">
            {fileProgress.map((file, i) => (
              <div 
                key={i}
                className={`flex items-center gap-3 p-3 rounded-lg border transition-colors ${
                  file.status === "completed" ? "bg-green-50 border-green-200" :
                  file.status === "transforming" || file.status === "analyzing" ? "bg-blue-50 border-blue-200" :
                  file.status === "failed" ? "bg-red-50 border-red-200" :
                  "bg-gray-50 border-gray-200"
                }`}
              >
                {file.status === "completed" ? (
                  <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0" />
                ) : file.status === "transforming" || file.status === "analyzing" ? (
                  <Loader2 className="h-5 w-5 text-blue-600 animate-spin flex-shrink-0" />
                ) : file.status === "failed" ? (
                  <XCircle className="h-5 w-5 text-red-600 flex-shrink-0" />
                ) : (
                  <Clock className="h-5 w-5 text-gray-400 flex-shrink-0" />
                )}
                
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                  <div className="flex items-center gap-2 mt-1">
                    {file.records && (
                      <span className="text-xs text-gray-500">{file.records} records</span>
                    )}
                    {file.batches_total && file.status === "transforming" && (
                      <span className="text-xs text-blue-600">
                        Batch {file.batches_done || 0}/{file.batches_total}
                      </span>
                    )}
                  </div>
                </div>

                {/* Mini progress bar */}
                {(file.status === "transforming" || file.status === "analyzing") && (
                  <div className="w-20 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-600 transition-all"
                      style={{ width: `${file.progress}%` }}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Logs section */}
        <div className="border-t border-gray-200">
          <button
            onClick={() => setShowLogs(!showLogs)}
            className="w-full px-6 py-3 flex items-center justify-between text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            <span>Logs ({logs.length} entries)</span>
            {showLogs ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
          
          {showLogs && (
            <div className="max-h-40 overflow-y-auto bg-gray-900 p-4 font-mono text-xs">
              {logs.length === 0 ? (
                <p className="text-gray-500">Waiting for logs...</p>
              ) : (
                logs.slice(-50).map((log, i) => (
                  <div key={i} className="text-gray-300 whitespace-pre-wrap">{log}</div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            {status === "running" && currentStage}
            {status === "completed" && "✅ All files transformed successfully!"}
            {status === "failed" && "❌ Transformation failed"}
          </div>
          {(status === "completed" || status === "failed" || status === "cancelled") && onClose && (
            <button
              onClick={onClose}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
            >
              Close
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
