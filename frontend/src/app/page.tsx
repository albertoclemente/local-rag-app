'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { AppHeader } from '@/components/app-header'
import { Sidebar } from '@/components/sidebar'
import { ChatView } from '@/components/chat-view'
import { SourcesPanel } from '@/components/sources-panel'
import { StatusBar } from '@/components/status-bar'
import type { Citation, SourceInfo } from '@/types'

export default function HomePage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [sourcesOpen, setSourcesOpen] = useState(false)
  const [currentSources, setCurrentSources] = useState<SourceInfo[]>([])
  const [currentCitations, setCurrentCitations] = useState<Citation[]>([])

  const handleSourcesUpdate = (sources: SourceInfo[], citations: Citation[]) => {
    console.log('🏠 HomePage: Updating sources state:', {
      sourcesCount: sources.length,
      citationsCount: citations.length,
      sources: sources,
      citations: citations
    })
    setCurrentSources(sources)
    setCurrentCitations(citations)
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div
        className={cn(
          'transition-all duration-300 ease-in-out bg-white border-r border-gray-200',
          sidebarOpen ? 'w-80' : 'w-16'
        )}
      >
        <Sidebar 
          isOpen={sidebarOpen} 
          onToggle={() => setSidebarOpen(!sidebarOpen)} 
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <AppHeader 
          onToggleSources={() => setSourcesOpen(!sourcesOpen)}
          sourcesOpen={sourcesOpen}
        />

        {/* Main Panel */}
        <div className="flex-1 flex overflow-hidden">
          {/* Chat View */}
          <div className="flex-1 flex flex-col">
            <ChatView onSourcesUpdate={handleSourcesUpdate} />
          </div>

          {/* Sources Panel */}
          <div
            className={cn(
              'transition-all duration-300 ease-in-out bg-white border-l border-gray-200',
              sourcesOpen ? 'w-96' : 'w-0 overflow-hidden'
            )}
          >
            {sourcesOpen && (
              <SourcesPanel 
                sources={currentSources} 
                citations={currentCitations} 
              />
            )}
          </div>
        </div>

        {/* Status Bar */}
        <StatusBar />
      </div>
    </div>
  )
}
