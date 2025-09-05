import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi, queryApi, systemApi } from '@/lib/api'
import type {
  Document,
  DocumentUploadRequest,
  DocumentUpdateRequest,
  QueryRequest,
  Settings
} from '@/types'
import toast from 'react-hot-toast'

// Query Keys
export const queryKeys = {
  documents: ['documents'] as const,
  document: (id: string) => ['documents', id] as const,
  systemStatus: ['system', 'status'] as const,
  settings: ['system', 'settings'] as const,
  health: ['system', 'health'] as const,
}

// Document Hooks
export function useDocuments() {
  return useQuery({
    queryKey: queryKeys.documents,
    queryFn: documentsApi.getDocuments,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: queryKeys.document(id),
    queryFn: () => documentsApi.getDocument(id),
    enabled: !!id,
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: documentsApi.uploadDocument,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents })
      toast.success(`Document "${data.filename}" uploaded successfully`)
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to upload document'
      toast.error(message)
    },
  })
}

export function useUpdateDocument() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: DocumentUpdateRequest }) =>
      documentsApi.updateDocument(id, data),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents })
      queryClient.invalidateQueries({ queryKey: queryKeys.document(variables.id) })
      toast.success(`Document "${data.filename}" updated successfully`)
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to update document'
      toast.error(message)
    },
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: documentsApi.deleteDocument,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents })
      queryClient.removeQueries({ queryKey: queryKeys.document(id) })
      toast.success('Document deleted successfully')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to delete document'
      toast.error(message)
    },
  })
}

export function useReindexDocument() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: documentsApi.reindexDocument,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents })
      queryClient.invalidateQueries({ queryKey: queryKeys.document(id) })
      toast.success('Document reindexed successfully')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to reindex document'
      toast.error(message)
    },
  })
}

// Query Hook
export function useSubmitQuery() {
  return useMutation({
    mutationFn: queryApi.query,
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to process query'
      toast.error(message)
    },
  })
}

// System Hooks
export function useSystemStatus() {
  return useQuery({
    queryKey: queryKeys.systemStatus,
    queryFn: systemApi.getStatus,
    refetchInterval: 10000, // Refetch every 10 seconds
    staleTime: 5000, // Consider stale after 5 seconds
  })
}

export function useSettings() {
  return useQuery({
    queryKey: queryKeys.settings,
    queryFn: systemApi.getSettings,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useUpdateSettings() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: systemApi.updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settings })
      toast.success('Settings updated successfully')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to update settings'
      toast.error(message)
    },
  })
}

export function useHealthCheck() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: systemApi.healthCheck,
    refetchInterval: 30000, // Check every 30 seconds
    retry: 3,
    staleTime: 10000,
  })
}
