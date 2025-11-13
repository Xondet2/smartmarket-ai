"use client"

import { useEffect, useState } from "react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react"
import { api } from "@/lib/api"

export function BackendStatus() {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking")

  useEffect(() => {
    const checkBackend = async () => {
      try {
        await api.healthCheck()
        setStatus("online")
      } catch (error) {
        setStatus("offline")
      }
    }

    checkBackend()
    const interval = setInterval(checkBackend, 10000) // Check every 10 seconds

    return () => clearInterval(interval)
  }, [])

  if (status === "checking") {
    return (
      <Alert className="border-blue-500/50 bg-blue-500/10 neon-panel gradient-border">
        <Loader2 className="h-4 w-4 animate-spin neon-icon" />
        <AlertTitle>Checking backend connection...</AlertTitle>
      </Alert>
    )
  }

  if (status === "offline") {
    return (
      <Alert variant="destructive" className="neon-panel gradient-border">
        <AlertCircle className="h-4 w-4 neon-icon" />
        <AlertTitle>Backend server is offline</AlertTitle>
        <AlertDescription>
          Make sure the FastAPI server is running. Open a terminal in the <code>backend</code> folder and run:
          <pre className="mt-2 rounded bg-black/50 p-2 text-xs">python main.py</pre>
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <Alert className="border-green-500/50 bg-green-500/10 neon-panel gradient-border">
      <CheckCircle2 className="h-4 w-4 text-green-500 neon-icon" />
      <AlertTitle className="text-green-500">Backend connected</AlertTitle>
      <AlertDescription>API server is running and ready</AlertDescription>
    </Alert>
  )
}
