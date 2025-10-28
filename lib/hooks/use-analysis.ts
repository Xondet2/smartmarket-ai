"use client"

import { useState, useCallback } from "react"
import { api, type AnalysisResult } from "@/lib/api"

export function useAnalysis() {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [analysisData, setAnalysisData] = useState<AnalysisResult | null>(null)

  const startAnalysis = useCallback(async (productUrl: string, platform = "amazon") => {
    setIsAnalyzing(true)
    setError(null)
    setAnalysisData(null)

    try {
      const response = await api.analyzeProduct({ product_url: productUrl, platform })

      // Poll for results
      await pollForResults(response.product_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze product")
      setIsAnalyzing(false)
    }
  }, [])

  const pollForResults = async (productId: number) => {
    let attempts = 0
    const maxAttempts = 30
    const pollInterval = 2000

    const poll = async () => {
      try {
        const data = await api.getAnalysis(productId)
        setAnalysisData(data)
        setIsAnalyzing(false)
      } catch (err) {
        if (attempts < maxAttempts) {
          attempts++
          setTimeout(poll, pollInterval)
        } else {
          setError("Analysis timeout - please try again")
          setIsAnalyzing(false)
        }
      }
    }

    // Wait 3 seconds before first poll to allow scraping to start
    setTimeout(poll, 3000)
  }

  const reset = useCallback(() => {
    setIsAnalyzing(false)
    setError(null)
    setAnalysisData(null)
  }, [])

  return {
    isAnalyzing,
    error,
    analysisData,
    startAnalysis,
    reset,
  }
}
