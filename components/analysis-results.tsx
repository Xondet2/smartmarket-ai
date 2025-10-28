"use client"

import { Card } from "@/components/ui/card"
import { SentimentChart } from "@/components/sentiment-chart"
import { KeywordsCloud } from "@/components/keywords-cloud"
import { PriceComparison } from "@/components/price-comparison"
import { TrendingUp, TrendingDown, Minus, Star } from "lucide-react"
import type { AnalysisResult } from "@/lib/api"

interface AnalysisResultsProps {
  data: AnalysisResult
}

export function AnalysisResults({ data }: AnalysisResultsProps) {
  const getSentimentIcon = (label: string) => {
    switch (label) {
      case "positive":
        return <TrendingUp className="h-5 w-5 text-green-500" />
      case "negative":
        return <TrendingDown className="h-5 w-5 text-red-500" />
      default:
        return <Minus className="h-5 w-5 text-yellow-500" />
    }
  }

  const getSentimentColor = (label: string) => {
    switch (label) {
      case "positive":
        return "text-green-500"
      case "negative":
        return "text-red-500"
      default:
        return "text-yellow-500"
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h2 className="mb-2 text-2xl font-bold text-foreground">Analysis Results</h2>
        <p className="text-muted-foreground">Based on {data.total_reviews} customer reviews</p>
      </div>

      {/* Overall Sentiment */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="mb-2 text-sm font-medium text-muted-foreground">Overall Sentiment</p>
            <div className="flex items-center gap-3">
              {getSentimentIcon(data.sentiment_label)}
              <span className={`text-3xl font-bold capitalize ${getSentimentColor(data.sentiment_label)}`}>
                {data.sentiment_label}
              </span>
            </div>
          </div>
          <div className="text-right">
            <p className="mb-2 text-sm font-medium text-muted-foreground">Sentiment Score</p>
            <div className="flex items-center gap-2">
              <Star className="h-6 w-6 fill-primary text-primary" />
              <span className="text-3xl font-bold text-foreground">{(data.avg_sentiment * 5).toFixed(1)}</span>
              <span className="text-muted-foreground">/5.0</span>
            </div>
          </div>
        </div>
      </Card>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="p-6">
          <p className="mb-2 text-sm font-medium text-muted-foreground">Positive Reviews</p>
          <p className="text-3xl font-bold text-green-500">{data.positive_count}</p>
          <p className="text-sm text-muted-foreground">
            {((data.positive_count / data.total_reviews) * 100).toFixed(1)}%
          </p>
        </Card>

        <Card className="p-6">
          <p className="mb-2 text-sm font-medium text-muted-foreground">Neutral Reviews</p>
          <p className="text-3xl font-bold text-yellow-500">{data.neutral_count}</p>
          <p className="text-sm text-muted-foreground">
            {((data.neutral_count / data.total_reviews) * 100).toFixed(1)}%
          </p>
        </Card>

        <Card className="p-6">
          <p className="mb-2 text-sm font-medium text-muted-foreground">Negative Reviews</p>
          <p className="text-3xl font-bold text-red-500">{data.negative_count}</p>
          <p className="text-sm text-muted-foreground">
            {((data.negative_count / data.total_reviews) * 100).toFixed(1)}%
          </p>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <SentimentChart data={data} />
        <KeywordsCloud keywords={data.keywords} />
      </div>

      {/* Price Comparison */}
      {data.price_data && Object.keys(data.price_data).length > 0 && <PriceComparison prices={data.price_data} />}
    </div>
  )
}
