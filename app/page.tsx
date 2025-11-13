"use client"

import { useEffect, useState } from "react"
import { SearchBar } from "@/components/search-bar"
import { AnalysisResults } from "@/components/analysis-results"
import { RecentAnalyses } from "@/components/recent-analyses"
import { SearchResults } from "@/components/search-results"
import { BackendStatus } from "@/components/backend-status"
import { UserMenu } from "@/components/user-menu"
import { Sparkles, Home as HomeIcon, Box, Brain, Database, Settings as SettingsIcon, Users, BarChart3 } from "lucide-react"
import type { SearchResult, AnalysisResult } from "@/lib/api"
import {
  SidebarProvider,
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarInset,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarSeparator,
} from "@/components/ui/sidebar"

export default function Home() {
  const [analysisData, setAnalysisData] = useState<AnalysisResult | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const apiUrl = process.env.NEXT_PUBLIC_API_URL

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
    <SidebarProvider>
      <Sidebar side="left" variant="floating" collapsible="icon">
        <SidebarHeader>
          <div className="px-4 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/20 neon-icon">
                <BarChart3 className="h-6 w-6 text-primary" />
              </div>
              <div>
                <div className="text-xl font-bold text-primary">Analytics</div>
              </div>
            </div>
          </div>
        </SidebarHeader>
        <SidebarContent>
          <div className="px-3">
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton isActive className="neon-panel">
                  <HomeIcon className="h-4 w-4" />
                  Dashboard
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton>
                  <Box className="h-4 w-4" />
                  Products
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton>
                  <Brain className="h-4 w-4" />
                  Analysis
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton>
                  <Database className="h-4 w-4" />
                  DB Diagram
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton>
                  <SettingsIcon className="h-4 w-4" />
                  Settings
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
            <SidebarSeparator className="my-4" />
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton>
                  <Users className="h-4 w-4" />
                  Admin Panel
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </div>
        </SidebarContent>
        <SidebarFooter>
          <div className="px-4 py-4 text-xs text-muted-foreground">Analytics Platform v1.0.0</div>
        </SidebarFooter>
      </Sidebar>
      <SidebarInset>
        <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border header-gradient backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary neon-icon">
                <Sparkles className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-foreground">DBVision</h1>
                <p className="text-sm text-muted-foreground">Intelligent Product Analysis</p>
              </div>
            </div>
            <UserMenu />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {apiUrl && (
          <div className="mb-8">
            <BackendStatus />
          </div>
        )}

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
      <footer className="mt-16 border-t border-border bg-card/50 py-8 gradient-border neon-panel">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>DBVision - Powered by FastAPI, React, and Transformers</p>
        </div>
      </footer>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
