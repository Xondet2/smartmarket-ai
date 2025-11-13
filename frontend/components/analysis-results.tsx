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
        <div className="flex items-start gap-4">
          {data.product_image_url && (
            <img
              src={data.product_image_url}
              alt={data.product_name || 'Product image'}
              className="h-16 w-16 flex-shrink-0 rounded-md object-cover"
            />
          )}
          <div className="flex-1">
            <h2 className="mb-1 text-2xl font-bold text-foreground">Analysis Results</h2>
            {data.product_name && (
              <p className="mb-1 text-sm text-muted-foreground">Product: {data.product_name}</p>
            )}
            {typeof data.product_price === 'number' && (
              <p className="mb-1 text-sm text-muted-foreground">Price: ${data.product_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
            )}
            {typeof data.product_rating === 'number' && (
              <p className="text-sm text-muted-foreground">Official Rating: {data.product_rating.toFixed(1)} / 5.0</p>
            )}
            <p className="text-muted-foreground">Based on {data.total_reviews} customer reviews</p>
          </div>
        </div>
      </div>

      {/* Overall Sentiment */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="mb-2 text-sm font-medium text-muted-foreground">Overall Sentiment</p>
            <div className="flex items-center gap-3">
              {getSentimentIcon(data.sentiment_label)}
              <span className={`text-3xl font-bold capitalize ${getSentimentColor(data.sentiment_label)} neon-number`}>
                {data.sentiment_label}
              </span>
            </div>
          </div>
          <div className="text-right">
            <p className="mb-2 text-sm font-medium text-muted-foreground">Sentiment Score</p>
            <div className="flex items-center gap-2">
              <Star className="h-6 w-6 fill-primary text-primary" />
              <span className="text-3xl font-bold text-foreground neon-number">{(data.avg_sentiment * 5).toFixed(1)}</span>
              <span className="text-muted-foreground">/5.0</span>
            </div>
          </div>
        </div>
      </Card>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="p-6">
          <p className="mb-2 text-sm font-medium text-muted-foreground">Positive Reviews</p>
          <p className="text-3xl font-bold text-green-500 neon-number">{data.positive_count}</p>
          <p className="text-sm text-muted-foreground">
            {data.total_reviews ? ((data.positive_count / data.total_reviews) * 100).toFixed(1) : '0.0'}%
          </p>
        </Card>

        <Card className="p-6">
          <p className="mb-2 text-sm font-medium text-muted-foreground">Neutral Reviews</p>
          <p className="text-3xl font-bold text-yellow-500 neon-number">{data.neutral_count}</p>
          <p className="text-sm text-muted-foreground">
            {data.total_reviews ? ((data.neutral_count / data.total_reviews) * 100).toFixed(1) : '0.0'}%
          </p>
        </Card>

        <Card className="p-6">
          <p className="mb-2 text-sm font-medium text-muted-foreground">Negative Reviews</p>
          <p className="text-3xl font-bold text-red-500 neon-number">{data.negative_count}</p>
          <p className="text-sm text-muted-foreground">
            {data.total_reviews ? ((data.negative_count / data.total_reviews) * 100).toFixed(1) : '0.0'}%
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
