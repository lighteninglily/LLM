"use client"

import { useState, useEffect } from "react"
import { FolderOpen, Rocket, Building2, Search, Home, ArrowLeft } from "lucide-react"
import Link from "next/link"
import { FileSelector } from "@/components/file-selector"
import { TransformProgress } from "@/components/transform-progress"
import { DirectoryBrowser } from "@/components/directory-browser"
import { fetchAPI } from "@/lib/utils"

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

interface JobInfo {
  job_id: string
  status: string
  progress: number
  current_file: string | null
  total_files: number
  completed_files: number
}

export default function PipelinePage() {
  const [files, setFiles] = useState<FileInfo[]>([])
  const [directories, setDirectories] = useState<DirectoryInfo[]>([])
  const [currentDirectory, setCurrentDirectory] = useState<string>("")
  const [selectedFiles, setSelectedFiles] = useState<string[]>([])
  const [uploadedFiles, setUploadedFiles] = useState<FileInfo[]>([])
  const [clientName, setClientName] = useState("")
  const [customPath, setCustomPath] = useState("")
  const [currentJob, setCurrentJob] = useState<JobInfo | null>(null)
  const [logs, setLogs] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [showProgress, setShowProgress] = useState(false)
  const [showBrowser, setShowBrowser] = useState(false)

  const databaseName = clientName
    ? clientName.toLowerCase().replace(/[^a-z0-9]+/g, '_') + '_kb'
    : 'client_data_kb'

  useEffect(() => {
    loadDirectories()
    loadFiles()
  }, [])

  useEffect(() => {
    let interval: NodeJS.Timeout
    if (currentJob && ["pending", "running"].includes(currentJob.status)) {
      interval = setInterval(async () => {
        try {
          const job = await fetchAPI<JobInfo>(`/api/jobs/${currentJob.job_id}`)
          setCurrentJob(job)
          
          const logsData = await fetchAPI<{ logs: string[] }>(
            `/api/jobs/${currentJob.job_id}/logs?limit=50`
          )
          setLogs(logsData.logs)
          
          if (!["pending", "running"].includes(job.status)) {
            clearInterval(interval)
          }
        } catch (e) {
          console.error("Failed to fetch job status:", e)
        }
      }, 2000)
    }
    return () => clearInterval(interval)
  }, [currentJob?.job_id, currentJob?.status])

  async function loadDirectories() {
    try {
      const data = await fetchAPI<{ directories: DirectoryInfo[] }>("/api/files/directories")
      setDirectories(data.directories)
      if (data.directories.length > 0 && !currentDirectory) {
        setCurrentDirectory(data.directories[0].path)
      }
    } catch (e) {
      console.error("Failed to load directories:", e)
    }
  }

  async function loadFiles(directory?: string) {
    try {
      const url = directory 
        ? `/api/files/sources?directory=${encodeURIComponent(directory)}`
        : "/api/files/sources"
      const data = await fetchAPI<{ files: FileInfo[] }>(url)
      setFiles(data.files)
    } catch (e) {
      console.error("Failed to load files:", e)
    }
  }

  async function handleDirectoryChange(dir: string) {
    setCurrentDirectory(dir)
    setSelectedFiles([])
    await loadFiles(dir)
  }

  function handleFilesDropped(droppedFiles: File[]) {
    const newFiles: FileInfo[] = droppedFiles.map(f => ({
      name: f.name,
      path: `uploaded:${f.name}`,
      size: f.size,
      records: null,
      modified: new Date().toISOString()
    }))
    setUploadedFiles(prev => [...prev, ...newFiles])
    setFiles(prev => [...prev, ...newFiles])
  }

  async function handleTransform() {
    if (selectedFiles.length === 0) return
    
    setLoading(true)
    setShowProgress(true)
    try {
      const response = await fetchAPI<{ job_id: string; status: string; message: string }>(
        "/api/transform/start",
        {
          method: "POST",
          body: JSON.stringify({
            files: selectedFiles,
            database_name: databaseName,
            enable_kg: true,
          }),
        }
      )
      setCurrentJob({
        job_id: response.job_id,
        status: response.status,
        progress: 0,
        current_file: null,
        total_files: selectedFiles.length,
        completed_files: 0,
      })
      setLogs([])
    } catch (e) {
      console.error("Failed to start transform:", e)
      setShowProgress(false)
    } finally {
      setLoading(false)
    }
  }

  async function handlePathLoad() {
    if (!customPath) return
    setCurrentDirectory(customPath)
    setSelectedFiles([])
    await loadFiles(customPath)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="container mx-auto px-6 py-4 max-w-5xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Link
                href="/"
                className="p-2 hover:bg-gray-100 rounded-lg transition"
              >
                <ArrowLeft className="h-5 w-5 text-gray-600" />
              </Link>
              <div className="p-2 bg-blue-600 rounded-xl">
                <Rocket className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Data Pipeline</h1>
                <p className="text-sm text-gray-500">Transform CSV files for AI analysis</p>
              </div>
            </div>
            <Link
              href="/"
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 text-sm font-medium transition"
            >
              <Home className="h-4 w-4" />
              Home
            </Link>
          </div>
        </div>
      </header>
      
      <main className="container mx-auto px-6 py-8 max-w-5xl">
        {/* Step 1: Client Info */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Building2 className="h-5 w-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">1. Client Information</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Client Name</label>
              <input
                type="text"
                value={clientName}
                onChange={(e) => setClientName(e.target.value)}
                placeholder="e.g. ACME Manufacturing"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Database Name</label>
              <div className="px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-600">
                {databaseName}
              </div>
            </div>
          </div>
        </div>

        {/* Step 2: Data Location */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <FolderOpen className="h-5 w-5 text-blue-600" />
              <h2 className="text-lg font-semibold text-gray-900">2. Select Data Location</h2>
            </div>
            <button
              onClick={() => setShowBrowser(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 text-sm font-medium shadow-md"
            >
              <Search className="h-4 w-4" />
              Browse...
            </button>
          </div>
          
          {/* Current path display */}
          {currentDirectory && (
            <div className="mb-4 px-4 py-3 bg-blue-50 border border-blue-200 rounded-xl">
              <p className="text-xs text-blue-600 font-medium mb-1">Selected Directory</p>
              <p className="text-sm font-mono text-blue-900 truncate">{currentDirectory}</p>
            </div>
          )}

          {/* Quick directory buttons */}
          <div className="flex flex-wrap gap-2 mb-4">
            {directories.map((dir) => (
              <button
                key={dir.path}
                onClick={() => handleDirectoryChange(dir.path)}
                className={`px-4 py-2 text-sm font-medium rounded-xl transition-all ${
                  currentDirectory === dir.path
                    ? "bg-blue-600 text-white shadow-md"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {dir.name} ({dir.file_count})
              </button>
            ))}
          </div>

          {/* Custom path input */}
          <div className="flex gap-2">
            <input
              type="text"
              value={customPath}
              onChange={(e) => setCustomPath(e.target.value)}
              placeholder="Or enter path: /home/client/data"
              className="flex-1 px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
              onKeyDown={(e) => e.key === "Enter" && handlePathLoad()}
            />
            <button
              onClick={handlePathLoad}
              className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 text-sm font-medium"
            >
              Load
            </button>
          </div>
        </div>

        {/* Step 3: Select Files */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden mb-6">
          <FileSelector
            files={files}
            selectedFiles={selectedFiles}
            onSelectionChange={setSelectedFiles}
            directories={[]}
            currentDirectory={currentDirectory}
            onDirectoryChange={handleDirectoryChange}
            onFilesDropped={handleFilesDropped}
          />
        </div>

        {/* Transform Button */}
        <div className="flex justify-center">
          <button
            onClick={handleTransform}
            disabled={selectedFiles.length === 0 || loading || !clientName}
            className="px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-2xl font-semibold text-lg shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-3"
          >
            <Rocket className="h-5 w-5" />
            {loading ? "Starting..." : `Transform ${selectedFiles.length} Files`}
          </button>
        </div>

        {selectedFiles.length === 0 && (
          <p className="text-center text-gray-500 mt-4">Select files above to transform</p>
        )}
        {!clientName && selectedFiles.length > 0 && (
          <p className="text-center text-amber-600 mt-4">Enter client name to continue</p>
        )}
      </main>

      {/* Progress Modal */}
      {showProgress && currentJob && (
        <TransformProgress
          jobId={currentJob.job_id}
          files={selectedFiles}
          status={currentJob.status as any}
          logs={logs}
          onClose={() => setShowProgress(false)}
        />
      )}

      {/* Directory Browser Modal */}
      {showBrowser && (
        <DirectoryBrowser
          initialPath={currentDirectory || "/home"}
          onDirectorySelect={(path) => {
            handleDirectoryChange(path)
            setCustomPath(path)
          }}
          onClose={() => setShowBrowser(false)}
        />
      )}
    </div>
  )
}
