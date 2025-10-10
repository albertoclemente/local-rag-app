'use client'

import React, { useState } from 'react'
import { useDocuments, useUploadDocument } from '@/hooks/api'
import { FileText, Upload, Search, Tag, MoreVertical, Trash2, RefreshCw, Plus, X } from 'lucide-react'
import { cn, formatFileSize, formatTimestamp } from '@/lib/utils'
import type { Document } from '@/types'

interface DocumentsPanelProps {
  isOpen?: boolean
}

export function DocumentsPanel({ isOpen = true }: DocumentsPanelProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTag, setSelectedTag] = useState<string | null>(null)
  const [showUpload, setShowUpload] = useState(false)
  const fileInputRef = React.useRef<HTMLInputElement>(null)
  
  const { data: documentsData, isLoading, error } = useDocuments()
  const uploadDocument = useUploadDocument()

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      await uploadDocument.mutateAsync({
        file,
        title: file.name
      })
      // Reset the input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      setShowUpload(false)
    } catch (error) {
      console.error('Upload failed:', error)
    }
  }

  const documents: Document[] = Array.isArray(documentsData) ? documentsData : []

  // Filter documents
  const filteredDocuments = documents.filter((doc: Document) => {
    if (!doc) return false
    
    const matchesSearch = searchQuery === '' || 
      (doc.name || doc.filename || doc.title || '').toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesTag = selectedTag === null || (doc.tags && doc.tags.includes(selectedTag))
    
    return matchesSearch && matchesTag
  })

  // Get all unique tags
  const allTags: string[] = Array.from(new Set(
    documents
      .filter((doc: Document) => doc && doc.tags)
      .flatMap((doc: Document) => doc.tags || [])
  ))

  if (!isOpen) {
    return null
  }

  return (
    <div className="h-full flex flex-col bg-white border-l border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <FileText className="h-5 w-5 mr-2 text-blue-600" />
            Documents
          </h3>
          <button
            onClick={handleUploadClick}
            className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            <Plus className="h-4 w-4 mr-1" />
            Upload
          </button>
        </div>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          accept=".pdf,.txt,.md,.doc,.docx,.pptx,.html,.htm,.png,.jpg,.jpeg,.tiff,.bmp,.asciidoc,.adoc"
          className="hidden"
        />

        {/* Search */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Tags Filter */}
        {allTags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            <button
              onClick={() => setSelectedTag(null)}
              className={cn(
                'px-2 py-1 text-xs rounded-full transition-colors',
                selectedTag === null
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              )}
            >
              All
            </button>
            {allTags.map((tag) => (
              <button
                key={tag}
                onClick={() => setSelectedTag(tag === selectedTag ? null : tag)}
                className={cn(
                  'px-2 py-1 text-xs rounded-full transition-colors',
                  selectedTag === tag
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                )}
              >
                {tag}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Documents List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-gray-500">
            <div className="animate-spin h-6 w-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-2" />
            <p className="text-sm">Loading documents...</p>
          </div>
        ) : error ? (
          <div className="p-4 text-center text-red-600">
            <p className="text-sm">Error loading documents</p>
            <p className="text-xs mt-1">{error instanceof Error ? error.message : 'Unknown error'}</p>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <FileText className="h-8 w-8 mx-auto mb-2 text-gray-400" />
            <p className="text-sm font-medium">
              {searchQuery || selectedTag ? 'No matching documents' : 'No documents yet'}
            </p>
            <p className="text-xs mt-1">
              {searchQuery || selectedTag ? 'Try a different search or filter' : 'Upload documents to get started'}
            </p>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {filteredDocuments.map((doc) => (
              <DocumentCard key={doc.id} document={doc} />
            ))}
          </div>
        )}
      </div>

      {/* Footer Stats */}
      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500 space-y-1">
          <div className="flex justify-between">
            <span>Total documents:</span>
            <span className="font-medium text-gray-700">{documents.length}</span>
          </div>
          <div className="flex justify-between">
            <span>Showing:</span>
            <span className="font-medium text-gray-700">{filteredDocuments.length}</span>
          </div>
          {documents.length > 0 && (
            <div className="flex justify-between">
              <span>Total size:</span>
              <span className="font-medium text-gray-700">
                {formatFileSize(documents.reduce((sum, doc) => sum + (doc.sizeBytes || doc.size || 0), 0))}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

interface DocumentCardProps {
  document: Document
}

function DocumentCard({ document }: DocumentCardProps) {
  const [showActions, setShowActions] = useState(false)

  return (
    <div
      className="p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50/50 transition-all group"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-1">
            <FileText className="h-4 w-4 text-blue-600 flex-shrink-0" />
            <span className="text-sm font-medium text-gray-900 truncate">
              {document.title || document.filename || document.name}
            </span>
          </div>
          
          <div className="flex items-center space-x-2 text-xs text-gray-500 mb-2">
            <span>{(document.type || document.file_type || 'DOC').toUpperCase()}</span>
            <span>•</span>
            <span>{formatFileSize(document.sizeBytes || document.size || 0)}</span>
          </div>
          
          {document.tags && document.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-2">
              {document.tags.map((tag, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-gray-100 text-gray-700"
                >
                  <Tag className="h-2.5 w-2.5 mr-0.5" />
                  {tag}
                </span>
              ))}
            </div>
          )}
          
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">
              {formatTimestamp(document.addedAt || document.upload_date)}
            </span>
            
            {(document.indexed || document.status === 'indexed') && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                Indexed
              </span>
            )}
          </div>
        </div>
        
        {showActions && (
          <button
            className="p-1 text-gray-400 hover:text-gray-600 ml-2"
            aria-label="Document actions"
          >
            <MoreVertical className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  )
}
