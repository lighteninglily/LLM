"use client"

import { Play, Square, Loader2 } from "lucide-react"

interface ActionButtonsProps {
  selectedCount: number
  onTransform: () => void
  onCancel: () => void
  loading: boolean
  hasActiveJob: boolean
}

export function ActionButtons({
  selectedCount,
  onTransform,
  onCancel,
  loading,
  hasActiveJob,
}: ActionButtonsProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Actions</h2>

      <div className="space-y-3">
        <button
          onClick={onTransform}
          disabled={selectedCount === 0 || loading || hasActiveJob}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              Starting...
            </>
          ) : (
            <>
              <Play className="h-5 w-5" />
              Transform {selectedCount > 0 && `(${selectedCount} files)`}
            </>
          )}
        </button>

        {hasActiveJob && (
          <button
            onClick={onCancel}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-red-50 text-red-600 font-medium rounded-lg hover:bg-red-100 transition-colors"
          >
            <Square className="h-5 w-5" />
            Cancel Job
          </button>
        )}
      </div>

      {selectedCount === 0 && (
        <p className="text-sm text-gray-500 mt-3 text-center">
          Select files to transform
        </p>
      )}
    </div>
  )
}
