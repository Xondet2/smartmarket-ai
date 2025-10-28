"use client"

import type React from "react"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Clock, TrendingUp, TrendingDown, Minus, Trash2, X } from "lucide-react"
import { useRecentAnalyses } from "@/lib/hooks/use-recent-analyses"
import { api } from "@/lib/api"
import { useState } from "react"

interface RecentAnalysesProps {
  onSelectAnalysis: (data: any) => void
}

export function RecentAnalyses({ onSelectAnalysis }: RecentAnalysesProps) {
  const { analyses, isLoading, error, refresh } = useRecentAnalyses(6)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [clearingAll, setClearingAll] = useState(false)

  const getSentimentIcon = (label: string) => {
    switch (label) {
      case "positive":
        return <TrendingUp className="h-4 w-4 text-green-500" />
      case "negative":
        return <TrendingDown className="h-4 w-4 text-red-500" />
      default:
        return <Minus className="h-4 w-4 text-yellow-500" />
    }
  }

  const handleDelete = async (e: React.MouseEvent, analysisId: number) => {
    e.stopPropagation()
    if (!confirm("¿Estás seguro de que quieres eliminar este análisis?")) return

    try {
      setDeletingId(analysisId)
      await api.deleteAnalysis(analysisId)
      refresh()
    } catch (err) {
      alert("Error al eliminar el análisis")
    } finally {
      setDeletingId(null)
    }
  }

  const handleClearAll = async () => {
    if (!confirm("¿Estás seguro de que quieres eliminar todo el historial?")) return

    try {
      setClearingAll(true)
      await api.clearAllAnalyses()
      refresh()
    } catch (err) {
      alert("Error al limpiar el historial")
    } finally {
      setClearingAll(false)
    }
  }

  if (isLoading) {
    return (
      <div className="text-center">
        <p className="text-muted-foreground">Loading recent analyses...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center">
        <p className="text-destructive">{error}</p>
      </div>
    )
  }

  if (analyses.length === 0) {
    return null
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-xl font-semibold text-foreground">Análisis Recientes</h3>
        <Button
          variant="outline"
          size="sm"
          onClick={handleClearAll}
          disabled={clearingAll}
          className="gap-2 bg-transparent"
        >
          <Trash2 className="h-4 w-4" />
          Limpiar Historial
        </Button>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {analyses.map((analysis) => (
          <Card
            key={analysis.id}
            className="group relative cursor-pointer p-4 transition-colors hover:bg-muted/50"
            onClick={() => onSelectAnalysis(analysis)}
          >
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-2 top-2 h-8 w-8 opacity-0 transition-opacity group-hover:opacity-100"
              onClick={(e) => handleDelete(e, analysis.id)}
              disabled={deletingId === analysis.id}
            >
              <X className="h-4 w-4" />
            </Button>

            <h4 className="mb-2 line-clamp-2 pr-8 text-sm font-semibold text-foreground">{analysis.product_name}</h4>

            <div className="mb-3 flex items-start justify-between">
              <div className="flex items-center gap-2">
                {getSentimentIcon(analysis.sentiment_label)}
                <span className="text-sm font-medium capitalize text-foreground">{analysis.sentiment_label}</span>
              </div>
              <span className="text-lg font-bold text-foreground">{(analysis.avg_sentiment * 5).toFixed(1)}</span>
            </div>

            <p className="mb-2 text-sm text-muted-foreground">{analysis.total_reviews} reviews analyzed</p>

            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              {new Date(analysis.analyzed_at).toLocaleDateString()}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
