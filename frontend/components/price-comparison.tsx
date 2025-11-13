"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { DollarSign, TrendingDown } from "lucide-react"

interface PriceComparisonProps {
  prices: Record<string, number>
}

export function PriceComparison({ prices }: PriceComparisonProps) {
  const priceEntries = Object.entries(prices).sort((a, b) => a[1] - b[1])
  const lowestPrice = priceEntries[0]?.[1]
  const highestPrice = priceEntries[priceEntries.length - 1]?.[1]
  const savings = highestPrice - lowestPrice

  return (
    <Card className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-foreground">Price Comparison</h3>
        {savings > 0 && (
          <Badge variant="default" className="gap-1 neon-icon">
            <TrendingDown className="h-3 w-3" />
            <span className="neon-number">Save ${savings.toFixed(2)}</span>
          </Badge>
        )}
      </div>

      <div className="space-y-3">
        {priceEntries.map(([platform, price], index) => (
          <div
            key={platform}
            className="flex items-center justify-between rounded-lg border border-border bg-muted/50 p-4"
          >
            <div className="flex items-center gap-3">
              <DollarSign className="h-5 w-5 text-muted-foreground" />
              <span className="font-medium capitalize text-foreground">{platform}</span>
              {index === 0 && (
                <Badge variant="default" className="text-xs">
                  Best Price
                </Badge>
              )}
            </div>
            <span className="text-xl font-bold text-foreground neon-number">${price.toFixed(2)}</span>
          </div>
        ))}
      </div>
    </Card>
  )
}
