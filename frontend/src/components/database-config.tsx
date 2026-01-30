"use client"

import { Database } from "lucide-react"

interface DatabaseConfigProps {
  databaseName: string
  onDatabaseNameChange: (name: string) => void
  chunkSize: number
  onChunkSizeChange: (size: number) => void
  enableKG: boolean
  onEnableKGChange: (enabled: boolean) => void
}

export function DatabaseConfig({
  databaseName,
  onDatabaseNameChange,
  chunkSize,
  onChunkSizeChange,
  enableKG,
  onEnableKGChange,
}: DatabaseConfigProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <div className="flex items-center gap-2 mb-4">
        <Database className="h-5 w-5 text-blue-600" />
        <h2 className="text-lg font-semibold text-gray-900">
          Database Configuration
        </h2>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Database Name
          </label>
          <input
            type="text"
            value={databaseName}
            onChange={(e) => onDatabaseNameChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter database name"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Chunk Size (tokens)
          </label>
          <select
            value={chunkSize}
            onChange={(e) => onChunkSizeChange(Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value={256}>256</option>
            <option value={512}>512</option>
            <option value={1024}>1024</option>
            <option value={2048}>2048</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="enableKG"
            checked={enableKG}
            onChange={(e) => onEnableKGChange(e.target.checked)}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <label htmlFor="enableKG" className="text-sm text-gray-700">
            Enable Knowledge Graph
          </label>
        </div>
      </div>
    </div>
  )
}
