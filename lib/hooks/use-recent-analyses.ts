"use client"

import { useState, useEffect } from "react"
import { api, type AnalysisResult } from "@/lib/api"

export function useRecentAnalyses(limit = 6) {
  const [analyses, setAnalyses] = useState<AnalysisResult[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchAnalyses()
  }, [limit])

  const fetchAnalyses = async () => {
    try {
      setIsLoading(true)
      const data = await api.listAnalyses(limit)
      setAnalyses(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch analyses")
    } finally {
      setIsLoading(false)
    }
  }

  const refresh = () => {
    fetchAnalyses()
  }

  return {
    analyses,
    isLoading,
    error,
    refresh,
  }
}
