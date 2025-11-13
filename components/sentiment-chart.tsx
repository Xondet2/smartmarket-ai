"use client"

import { Card } from "@/components/ui/card"
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, LabelList } from "recharts"
 

interface SentimentChartProps {
  data: any
}

export function SentimentChart({ data }: SentimentChartProps) {
  const chartData = [
    { name: "Positive", value: Number(data?.positive_count) || 0, color: "#22e584" },
    { name: "Neutral", value: Number(data?.neutral_count) || 0, color: "#ffd43b" },
    { name: "Negative", value: Number(data?.negative_count) || 0, color: "#ff4d6d" },
  ]
  const total = chartData.reduce((acc, d) => acc + (Number(d.value) || 0), 0)
  const labelValueAccessor = (entry: any, _index: number): string => {
    const value = entry && typeof entry === 'object' && 'value' in entry ? Number((entry as any).value) : 0
    const payload = entry && typeof entry === 'object' && 'payload' in entry ? (entry as any).payload : undefined
    const name = payload && typeof payload === 'object' && 'name' in payload ? (payload as any).name : ''
    const p = total > 0 ? (value / total) * 100 : 0
    return `${name} ${p.toFixed(0)}%`
  }

  return (
    <Card className="p-6 gradient-border chart-neon">
      <h3 className="mb-4 text-lg font-semibold text-foreground">Sentiment Distribution</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            outerRadius={105}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
            <LabelList position="outside" dataKey="value" valueAccessor={labelValueAccessor} />
          </Pie>
          <Tooltip wrapperStyle={{ background: 'rgba(20,22,48,0.9)', borderRadius: 8, border: '1px solid rgba(120,150,255,0.3)', color: '#fff' }} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </Card>
  )
}
