'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, User, Bot } from 'lucide-react'
import { useSubmitQuery } from '@/hooks/api'
import { cn } from '@/lib/utils'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'
import type { ChatMessage, StreamingQueryResponse, Citation, SourceInfo } from '@/types'

interface ChatViewProps {
  onSourcesUpdate?: (sources: SourceInfo[], citations: Citation[]) => void
}

export function ChatView({ onSourcesUpdate }: ChatViewProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [sessionId] = useState(() => `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  
  const submitQuery = useSubmitQuery()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || submitQuery.isPending) return

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    const queryText = input.trim()
    setInput('')
    setIsStreaming(true)
    setStreamingContent('')

    try {
      const response = await submitQuery.mutateAsync({
        query: queryText,
        sessionId: sessionId,
        onStreamingStart: () => {
          console.log('🚀 Streaming started')
        },
        onStreamToken: (token: string) => {
          setStreamingContent(prev => prev + token)
        },
        onStreamingEnd: () => {
          console.log('✅ Streaming ended')
        }
      })

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toISOString(),
        citations: response.citations,
        query_id: response.query_id
      }

      setMessages(prev => [...prev, assistantMessage])

      // Update sources panel with the response data
      console.log('📝 ChatView: Response received:', {
        chunks: response.chunks,
        citations: response.citations,
        chunksLength: response.chunks?.length,
        citationsLength: response.citations?.length
      })
      
      if (onSourcesUpdate) {
        onSourcesUpdate(response.chunks || [], response.citations || [])
        console.log('📡 ChatView: Called onSourcesUpdate with:', response.chunks?.length, 'sources and', response.citations?.length, 'citations')
      }
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your query. Please try again.',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsStreaming(false)
      setStreamingContent('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [input])

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Bot className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium mb-2" style={{ color: '#000000' }}>
              Welcome to Local RAG
            </h3>
            <p className="text-gray-500 max-w-md">
              Ask questions about your uploaded documents. I'll search through them 
              and provide detailed answers with citations.
            </p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isStreaming && (
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-blue-600" />
                  </div>
                </div>
                <div className="flex-1">
                  <div className="bg-white rounded-lg border border-gray-200 px-4 py-3">
                    {streamingContent ? (
                      <div className="prose prose-sm max-w-none text-black">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm, remarkMath]}
                          rehypePlugins={[rehypeKatex]}
                          components={{
                            p: ({ children }) => <p className="mb-2 last:mb-0 text-black">{children}</p>,
                            strong: ({ children }) => <strong className="font-bold text-black">{children}</strong>,
                            ul: ({ children }) => <ul className="list-disc pl-4 mb-2 text-black">{children}</ul>,
                            ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 text-black">{children}</ol>,
                            li: ({ children }) => <li className="mb-1 text-black">{children}</li>,
                            h1: ({ children }) => <h1 className="text-xl font-bold mb-3 text-black">{children}</h1>,
                            h2: ({ children }) => <h2 className="text-lg font-bold mb-2 text-black">{children}</h2>,
                            h3: ({ children }) => <h3 className="text-base font-bold mb-2 text-black">{children}</h3>,
                            code: ({ children }) => <code className="bg-gray-100 px-1 rounded text-black font-mono text-sm">{children}</code>,
                            blockquote: ({ children }) => <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-700">{children}</blockquote>
                          }}
                        >
                          {streamingContent}
                        </ReactMarkdown>
                        <span className="inline-block w-2 h-4 bg-blue-600 animate-pulse ml-1" />
                      </div>
                    ) : (
                      <div className="flex items-center space-x-2">
                        <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                        <span className="text-sm text-gray-600">Thinking...</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white p-4">
        <form onSubmit={handleSubmit} className="flex space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents..."
              rows={1}
              className="w-full resize-none border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent max-h-32"
              style={{ color: '#000000' }}
              disabled={submitQuery.isPending}
            />
          </div>
          <button
            type="submit"
            disabled={!input.trim() || submitQuery.isPending}
            className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
          >
            {submitQuery.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </form>
      </div>
    </div>
  )
}

interface MessageBubbleProps {
  message: ChatMessage
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={cn(
      'flex space-x-3',
      isUser ? 'flex-row-reverse space-x-reverse' : ''
    )}>
      {/* Avatar */}
      <div className="flex-shrink-0">
        <div className={cn(
          'h-8 w-8 rounded-full flex items-center justify-center',
          isUser ? 'bg-gray-200' : 'bg-blue-100'
        )}>
          {isUser ? (
            <User className="h-4 w-4 text-gray-600" />
          ) : (
            <Bot className="h-4 w-4 text-blue-600" />
          )}
        </div>
      </div>

      {/* Message Content */}
      <div className="flex-1 max-w-3xl">
        <div className={cn(
          'rounded-lg px-4 py-3',
          isUser 
            ? 'bg-blue-600 text-white ml-auto'
            : 'bg-white border border-gray-200'
        )}>
          <div className="prose prose-sm max-w-none">
            {isUser ? (
              // For user messages, keep simple text formatting
              (message.content || '').split('\n').map((line, index) => (
                <p key={index} className={cn(
                  'mb-2 last:mb-0',
                  'text-white !text-white'
                )} style={{ color: 'white' }}>
                  {line}
                </p>
              ))
            ) : (
              // For assistant messages, render markdown
              <div className="text-black">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm, remarkMath]}
                  rehypePlugins={[rehypeKatex]}
                  components={{
                    p: ({ children }) => <p className="mb-2 last:mb-0 text-black">{children}</p>,
                    strong: ({ children }) => <strong className="font-bold text-black">{children}</strong>,
                    ul: ({ children }) => <ul className="list-disc pl-4 mb-2 text-black">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 text-black">{children}</ol>,
                    li: ({ children }) => <li className="mb-1 text-black">{children}</li>,
                    h1: ({ children }) => <h1 className="text-xl font-bold mb-3 text-black">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-lg font-bold mb-2 text-black">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-base font-bold mb-2 text-black">{children}</h3>,
                    code: ({ children }) => <code className="bg-gray-100 px-1 rounded text-black font-mono text-sm">{children}</code>,
                    blockquote: ({ children }) => <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-700">{children}</blockquote>
                  }}
                >
                  {message.content || ''}
                </ReactMarkdown>
              </div>
            )}
          </div>
        </div>

        {/* Timestamp */}
        <div className={cn(
          'text-xs text-gray-500 mt-1',
          isUser ? 'text-right' : 'text-left'
        )}>
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}
