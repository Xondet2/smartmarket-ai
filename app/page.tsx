"use client"

import { useEffect, useState } from "react"
import { SearchBar } from "@/components/search-bar"
import { AnalysisResults } from "@/components/analysis-results"
import { RecentAnalyses } from "@/components/recent-analyses"
import { SearchResults } from "@/components/search-results"
import { BackendStatus } from "@/components/backend-status"
import { UserMenu } from "@/components/user-menu"
import { Sparkles } from "lucide-react"
import type { SearchResult, AnalysisResult } from "@/lib/api"

export default function Home() {
  const [analysisData, setAnalysisData] = useState<AnalysisResult | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])

  const handleAnalysisComplete = (data: AnalysisResult) => {
    setAnalysisData(data)
    setIsAnalyzing(false)
  }

  const handleAnalysisStart = () => {
    setIsAnalyzing(true)
    setAnalysisData(null)
    setSearchResults([])
  }

  const handleSearchResults = (results: SearchResult[]) => {
    setSearchResults(results)
    setIsAnalyzing(false)
    setAnalysisData(null)
  }

  const handleAnalyzeFromSearch = async (url: string) => {
    setIsAnalyzing(true)
    setSearchResults([])

    try {
      const { api } = await import("@/lib/api")
      const response = await api.analyzeProduct({ product_url: url })

      setTimeout(async () => {
        try {
          const analysis = await api.getAnalysis(response.product_id)
          setAnalysisData(analysis)
          setIsAnalyzing(false)
        } catch (err) {
          setIsAnalyzing(false)
        }
      }, 3000)
    } catch (err) {
      setIsAnalyzing(false)
    }
  }

  // Ensure the header with charts is visible when selecting an analysis
  useEffect(() => {
    if (analysisData && !isAnalyzing) {
      try {
        window.scrollTo({ top: 0, behavior: "smooth" })
      } catch {}
    }
  }, [analysisData, isAnalyzing])

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
                <Sparkles className="h-6 w-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-foreground">SmartMarket AI</h1>
                <p className="text-sm text-muted-foreground">Intelligent Product Analysis</p>
              </div>
            </div>
            <UserMenu />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <BackendStatus />
        </div>

        {/* Hero Section */}
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-balance text-4xl font-bold">
            Analyze Products with <span className="text-primary">AI-Powered Insights</span>
          </h2>
          <p className="mx-auto max-w-2xl text-pretty text-lg text-muted-foreground">
            Get comprehensive sentiment analysis, price comparisons, and customer insights from e-commerce platforms in
            seconds.
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-12">
          <SearchBar
            onAnalysisComplete={handleAnalysisComplete}
            onAnalysisStart={handleAnalysisStart}
            onSearchResults={handleSearchResults}
          />
        </div>

        {/* Search Results */}
        {searchResults.length > 0 && !isAnalyzing && (
          <div className="mb-12">
            <SearchResults results={searchResults} onAnalyzeProduct={handleAnalyzeFromSearch} />
          </div>
        )}

        {/* Analysis Results */}
        {isAnalyzing && (
          <div className="mb-12">
            <div className="rounded-lg border border-border bg-card p-8 text-center">
              <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent" />
              <p className="text-lg font-medium text-foreground">Analyzing product...</p>
              <p className="text-sm text-muted-foreground">Scraping reviews and running AI analysis</p>
            </div>
          </div>
        )}

        {analysisData && !isAnalyzing && (
          <div className="mb-12">
            <AnalysisResults data={analysisData} />
          </div>
        )}

        {/* Recent Analyses */}
        {!isAnalyzing && searchResults.length === 0 && (
          <div>
            <RecentAnalyses onSelectAnalysis={setAnalysisData} />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t border-border bg-card/50 py-8">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>SmartMarket AI - Powered by FastAPI, React, and Transformers</p>
        </div>
      </footer>
    </div>
  )
}
