"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface KeywordsCloudProps {
  keywords: string[]
}

export function KeywordsCloud({ keywords }: KeywordsCloudProps) {
  return (
    <Card className="p-6 gradient-border">
      <h3 className="mb-4 text-lg font-semibold text-foreground">Top Keywords</h3>
      <div className="flex flex-wrap gap-2">
        {keywords.map((keyword, index) => (
          <Badge
            key={index}
            variant="secondary"
            className="px-3 py-1.5 text-sm"
            style={{
              fontSize: `${1 + (keywords.length - index) * 0.08}rem`,
            }}
          >
            {keyword}
          </Badge>
        ))}
      </div>
    </Card>
  )
}
