"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search, LinkIcon } from "lucide-react"
import { useAnalysis } from "@/lib/hooks/use-analysis"

interface SearchBarProps {
  onAnalysisComplete: (data: any) => void
  onAnalysisStart: () => void
  onSearchResults?: (results: any[]) => void
}

export function SearchBar({ onAnalysisComplete, onAnalysisStart, onSearchResults }: SearchBarProps) {
  const [input, setInput] = useState("")
  const { startAnalysis, isAnalyzing, analysisData, error } = useAnalysis()

  useEffect(() => {
    if (analysisData && !isAnalyzing) {
      onAnalysisComplete(analysisData)
    }
  }, [analysisData, isAnalyzing, onAnalysisComplete])

  const isUrl = (text: string) => {
    try {
      new URL(text)
      return true
    } catch {
      return text.includes("amazon.com") || text.includes("ebay.com") || text.includes("mercadolibre")
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!input.trim()) return

    onAnalysisStart()

    if (isUrl(input)) {
      // Analyze specific product URL
      await startAnalysis(input)
      setInput("")
    } else {
      // Search by product name across platforms
      try {
        const { api } = await import("@/lib/api")
        const results = await api.searchProducts(input)

        if (onSearchResults) {
          onSearchResults(results)
        }

        setInput("")
      } catch (err) {
        console.error("Search error:", err)
      }
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mx-auto max-w-3xl">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <LinkIcon className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Pega la URL de Mercado Libre"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="h-12 pl-10 text-base"
            disabled={isAnalyzing}
          />
        </div>
        <Button type="submit" size="lg" disabled={isAnalyzing || !input.trim()} className="h-12 px-8">
          <Search className="mr-2 h-5 w-5" />
          {isUrl(input) ? "Analyze" : "Search"}
        </Button>
      </div>
      {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
    </form>
  )
}
