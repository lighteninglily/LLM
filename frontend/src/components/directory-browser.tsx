"use client"

import { useState, useEffect } from "react"
import { 
  Folder, FileText, ChevronRight, ChevronUp, 
  Home, HardDrive, RefreshCw 
} from "lucide-react"
import { fetchAPI, formatBytes } from "@/lib/utils"

interface BrowseItem {
  name: string
  path: string
  type: "directory" | "file"
  csv_count?: number
  size?: number
  records?: number
}

interface BrowseResponse {
  current_path: string
  parent_path: string | null
  items: BrowseItem[]
}

interface DirectoryBrowserProps {
  onDirectorySelect: (path: string) => void
  onClose: () => void
  initialPath?: string
}

export function DirectoryBrowser({ 
  onDirectorySelect, 
  onClose,
  initialPath = "/home"
}: DirectoryBrowserProps) {
  const [currentPath, setCurrentPath] = useState(initialPath)
  const [items, setItems] = useState<BrowseItem[]>([])
  const [parentPath, setParentPath] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pathInput, setPathInput] = useState(initialPath)

  useEffect(() => {
    loadDirectory(currentPath)
  }, [currentPath])

  async function loadDirectory(path: string) {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchAPI<BrowseResponse>(
        `/api/files/browse?path=${encodeURIComponent(path)}`
      )
      setItems(data.items)
      setParentPath(data.parent_path)
      setCurrentPath(data.current_path)
      setPathInput(data.current_path)
    } catch (e: any) {
      setError(e.message || "Failed to load directory")
    } finally {
      setLoading(false)
    }
  }

  function handleItemClick(item: BrowseItem) {
    if (item.type === "directory") {
      setCurrentPath(item.path)
    }
  }

  function handleGoUp() {
    if (parentPath) {
      setCurrentPath(parentPath)
    }
  }

  function handlePathSubmit(e: React.FormEvent) {
    e.preventDefault()
    setCurrentPath(pathInput)
  }

  function handleSelectCurrent() {
    onDirectorySelect(currentPath)
    onClose()
  }

  const quickPaths = [
    { label: "Home", path: "/home", icon: Home },
    { label: "Root", path: "/", icon: HardDrive },
  ]

  const csvCount = items.filter(i => i.type === "file").length
  const dirCount = items.filter(i => i.type === "directory").length

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 bg-gray-50 rounded-t-2xl">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-gray-900">Select Directory</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-xl"
            >
              ×
            </button>
          </div>

          {/* Path input */}
          <form onSubmit={handlePathSubmit} className="flex gap-2">
            <input
              type="text"
              value={pathInput}
              onChange={(e) => setPathInput(e.target.value)}
              className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
            />
            <button
              type="submit"
              className="px-3 py-2 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </form>

          {/* Quick paths */}
          <div className="flex gap-2 mt-3">
            {quickPaths.map((qp) => (
              <button
                key={qp.path}
                onClick={() => setCurrentPath(qp.path)}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
              >
                <qp.icon className="h-3 w-3" />
                {qp.label}
              </button>
            ))}
            {parentPath && (
              <button
                onClick={handleGoUp}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100"
              >
                <ChevronUp className="h-3 w-3" />
                Up
              </button>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-2">
          {loading ? (
            <div className="flex items-center justify-center py-12 text-gray-500">
              <RefreshCw className="h-5 w-5 animate-spin mr-2" />
              Loading...
            </div>
          ) : error ? (
            <div className="text-center py-12 text-red-500">
              {error}
            </div>
          ) : items.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              Empty directory
            </div>
          ) : (
            <div className="space-y-1">
              {items.map((item) => (
                <button
                  key={item.path}
                  onClick={() => handleItemClick(item)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors ${
                    item.type === "directory"
                      ? "hover:bg-blue-50"
                      : "hover:bg-gray-50 opacity-60 cursor-default"
                  }`}
                  disabled={item.type === "file"}
                >
                  {item.type === "directory" ? (
                    <Folder className="h-5 w-5 text-blue-500 flex-shrink-0" />
                  ) : (
                    <FileText className="h-5 w-5 text-gray-400 flex-shrink-0" />
                  )}
                  
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {item.name}
                    </p>
                    {item.type === "directory" && item.csv_count !== undefined && item.csv_count > 0 && (
                      <p className="text-xs text-blue-600">
                        {item.csv_count} CSV files
                      </p>
                    )}
                    {item.type === "file" && (
                      <p className="text-xs text-gray-500">
                        {item.size !== undefined && formatBytes(item.size)}
                        {item.records !== undefined && ` • ${item.records} records`}
                      </p>
                    )}
                  </div>

                  {item.type === "directory" && (
                    <ChevronRight className="h-4 w-4 text-gray-400" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50 rounded-b-2xl">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              {dirCount} folders, {csvCount} CSV files
            </div>
            <div className="flex gap-2">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSelectCurrent}
                disabled={csvCount === 0}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Select This Directory ({csvCount} files)
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
