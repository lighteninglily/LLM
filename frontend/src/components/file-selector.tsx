"use client"

import { useState, useCallback } from "react"
import { FileText, Check, Search, FolderOpen, Upload, X } from "lucide-react"
import { formatBytes } from "@/lib/utils"

interface FileInfo {
  name: string
  path: string
  size: number
  records: number | null
  modified: string
}

interface DirectoryInfo {
  path: string
  name: string
  file_count: number
}

interface FileSelectorProps {
  files: FileInfo[]
  selectedFiles: string[]
  onSelectionChange: (files: string[]) => void
  directories?: DirectoryInfo[]
  currentDirectory?: string
  onDirectoryChange?: (dir: string) => void
  onFilesDropped?: (files: File[]) => void
}

export function FileSelector({
  files,
  selectedFiles,
  onSelectionChange,
  directories = [],
  currentDirectory,
  onDirectoryChange,
  onFilesDropped,
}: FileSelectorProps) {
  const [search, setSearch] = useState("")
  const [isDragging, setIsDragging] = useState(false)
  const [customPath, setCustomPath] = useState("")
  const [showPathInput, setShowPathInput] = useState(false)

  const filteredFiles = files.filter((f) =>
    f.name.toLowerCase().includes(search.toLowerCase())
  )

  const toggleFile = (path: string) => {
    if (selectedFiles.includes(path)) {
      onSelectionChange(selectedFiles.filter((p) => p !== path))
    } else {
      onSelectionChange([...selectedFiles, path])
    }
  }

  const selectAll = () => {
    if (selectedFiles.length === filteredFiles.length) {
      onSelectionChange([])
    } else {
      onSelectionChange(filteredFiles.map((f) => f.path))
    }
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      f => f.name.endsWith('.csv') || f.name.endsWith('.txt')
    )
    
    if (droppedFiles.length > 0 && onFilesDropped) {
      onFilesDropped(droppedFiles)
    }
  }, [onFilesDropped])

  const handlePathSubmit = () => {
    if (customPath && onDirectoryChange) {
      onDirectoryChange(customPath)
      setShowPathInput(false)
      setCustomPath("")
    }
  }

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`transition-colors ${isDragging ? "ring-2 ring-blue-500 ring-inset" : ""}`}
    >
      {/* File List Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Source Files</h2>
          <span className="text-sm text-gray-500">
            {selectedFiles.length} of {files.length} selected
          </span>
        </div>

        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search files..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={selectAll}
            className="px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          >
            {selectedFiles.length === filteredFiles.length
              ? "Deselect All"
              : "Select All"}
          </button>
        </div>
      </div>

      <div className="max-h-[400px] overflow-y-auto">
        {filteredFiles.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No files found
          </div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {filteredFiles.map((file) => {
              const isSelected = selectedFiles.includes(file.path)
              return (
                <li
                  key={file.path}
                  onClick={() => toggleFile(file.path)}
                  className={`flex items-center gap-3 p-3 cursor-pointer transition-colors ${
                    isSelected
                      ? "bg-blue-50 hover:bg-blue-100"
                      : "hover:bg-gray-50"
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                      isSelected
                        ? "bg-blue-600 border-blue-600"
                        : "border-gray-300"
                    }`}
                  >
                    {isSelected && <Check className="h-3 w-3 text-white" />}
                  </div>
                  <FileText className="h-5 w-5 text-gray-400" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatBytes(file.size)}
                      {file.records !== null && ` • ${file.records} records`}
                    </p>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
