"use client"

import { CheckCircle, XCircle, Loader2, Clock } from "lucide-react"

interface JobInfo {
  job_id: string
  status: string
  progress: number
  current_file: string | null
  total_files: number
  completed_files: number
}

interface JobProgressProps {
  job: JobInfo
  logs: string[]
}

export function JobProgress({ job, logs }: JobProgressProps) {
  const statusConfig = {
    pending: {
      icon: Clock,
      color: "text-yellow-600",
      bgColor: "bg-yellow-50",
      label: "Pending",
    },
    running: {
      icon: Loader2,
      color: "text-blue-600",
      bgColor: "bg-blue-50",
      label: "Running",
      animate: true,
    },
    completed: {
      icon: CheckCircle,
      color: "text-green-600",
      bgColor: "bg-green-50",
      label: "Completed",
    },
    failed: {
      icon: XCircle,
      color: "text-red-600",
      bgColor: "bg-red-50",
      label: "Failed",
    },
    cancelled: {
      icon: XCircle,
      color: "text-gray-600",
      bgColor: "bg-gray-50",
      label: "Cancelled",
    },
  }

  const config = statusConfig[job.status as keyof typeof statusConfig] || statusConfig.pending
  const StatusIcon = config.icon

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${config.bgColor}`}>
              <StatusIcon
                className={`h-5 w-5 ${config.color} ${
                  config.animate ? "animate-spin" : ""
                }`}
              />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Job Progress
              </h2>
              <p className="text-sm text-gray-500">
                {config.label} • {job.completed_files}/{job.total_files} files
              </p>
            </div>
          </div>
          <span className="text-sm font-mono text-gray-500">
            ID: {job.job_id}
          </span>
        </div>

        {/* Progress bar */}
        <div className="mb-2">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600 truncate max-w-[70%]">
              {job.current_file || "Waiting..."}
            </span>
            <span className="text-gray-900 font-medium">
              {Math.round(job.progress)}%
            </span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all duration-300"
              style={{ width: `${job.progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Logs */}
      <div className="p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Logs</h3>
        <div className="bg-gray-900 rounded-lg p-3 max-h-[200px] overflow-y-auto font-mono text-xs">
          {logs.length === 0 ? (
            <p className="text-gray-500">Waiting for logs...</p>
          ) : (
            logs.map((log, i) => (
              <div key={i} className="text-gray-300 whitespace-pre-wrap">
                {log}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
