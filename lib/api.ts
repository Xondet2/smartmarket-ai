const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "")

export interface Product {
  id: number
  name: string
  platform: string
  url: string
  image_url?: string
  price?: number
  rating?: number
  created_at: string
}

export interface SearchResult {
  name: string
  price: number
  platform: string
  url: string
  rating?: number
  reviews_count?: number
}

export interface AnalysisResult {
  id: number
  product_id: number
  product_name: string // Added product_name field
  product_price?: number
  product_image_url?: string
  product_rating?: number
  avg_sentiment: number
  sentiment_label: string
  total_reviews: number
  positive_count: number
  negative_count: number
  neutral_count: number
  keywords: string[]
  price_data: Record<string, number> | null
  analyzed_at: string
}

export interface AnalysisRequest {
  product_url: string
  platform?: string
}

export interface AnalysisResponse {
  status: string
  message: string
  product_id: number
  product_url: string
  platform: string
}

class ApiService {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private getAuthHeaders(includeJsonContentType = false): HeadersInit {
    const token = typeof window !== "undefined" ? localStorage.getItem("smartmarket_token") : null
    const headers: HeadersInit = {}

    if (includeJsonContentType) {
      headers["Content-Type"] = "application/json"
    }

    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }

    return headers
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    const contentType = response.headers.get("content-type")

    if (contentType && contentType.includes("text/html")) {
      throw new Error(
        "Backend server is not responding. Make sure the FastAPI server is running on http://localhost:8000",
      )
    }

    if (!response.ok) {
      let errorMessage = `Request failed with status ${response.status}`

      try {
        const errorData = await response.json()
        errorMessage = errorData.detail || errorData.message || errorMessage
      } catch {
        errorMessage = response.statusText || errorMessage
      }

      throw new Error(errorMessage)
    }

    try {
      return await response.json()
    } catch (error) {
      throw new Error("Invalid response from server. Make sure the backend is running correctly.")
    }
  }

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "GET",
      headers: this.getAuthHeaders(false),
    })
    return this.handleResponse<T>(response)
  }

  async post<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "POST",
      headers: this.getAuthHeaders(true),
      body: JSON.stringify(data),
    })
    return this.handleResponse<T>(response)
  }

  async put<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "PUT",
      headers: this.getAuthHeaders(true),
      body: JSON.stringify(data),
    })
    return this.handleResponse<T>(response)
  }

  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "DELETE",
      headers: this.getAuthHeaders(false),
    })
    return this.handleResponse<T>(response)
  }

  async searchProducts(productName: string, platforms?: string[]): Promise<SearchResult[]> {
    const params = new URLSearchParams({ product_name: productName })
    if (platforms && platforms.length > 0) {
      platforms.forEach((p) => params.append("platforms", p))
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/products/search?${params}`)
      return this.handleResponse<SearchResult[]>(response)
    } catch (error) {
      if (error instanceof TypeError && error.message.includes("fetch")) {
        throw new Error("Cannot connect to backend. Make sure the server is running on http://localhost:8000")
      }
      throw error
    }
  }

  async analyzeProduct(request: AnalysisRequest): Promise<AnalysisResponse> {
    try {
      return await this.post<AnalysisResponse>("/api/analysis/analyze", request)
    } catch (error) {
      if (error instanceof TypeError && error.message.includes("fetch")) {
        throw new Error("Cannot connect to backend. Make sure the server is running on http://localhost:8000")
      }
      throw error
    }
  }

  async getAnalysis(productId: number): Promise<AnalysisResult> {
    try {
      const response = await fetch(`${this.baseUrl}/api/analysis/${productId}`)
      return this.handleResponse<AnalysisResult>(response)
    } catch (error) {
      if (error instanceof TypeError && error.message.includes("fetch")) {
        throw new Error("Cannot connect to backend. Make sure the server is running on http://localhost:8000")
      }
      throw error
    }
  }

  async listAnalyses(limit = 10): Promise<AnalysisResult[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/analysis/?limit=${limit}`)
      return this.handleResponse<AnalysisResult[]>(response)
    } catch (error) {
      if (error instanceof TypeError && error.message.includes("fetch")) {
        throw new Error("Cannot connect to backend. Make sure the server is running on http://localhost:8000")
      }
      throw error
    }
  }

  async getProduct(productId: number): Promise<Product> {
    try {
      const response = await fetch(`${this.baseUrl}/api/products/${productId}`)
      return this.handleResponse<Product>(response)
    } catch (error) {
      if (error instanceof TypeError && error.message.includes("fetch")) {
        throw new Error("Cannot connect to backend. Make sure the server is running on http://localhost:8000")
      }
      throw error
    }
  }

  async listProducts(limit = 10): Promise<Product[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/products/?limit=${limit}`)
      return this.handleResponse<Product[]>(response)
    } catch (error) {
      if (error instanceof TypeError && error.message.includes("fetch")) {
        throw new Error("Cannot connect to backend. Make sure the server is running on http://localhost:8000")
      }
      throw error
    }
  }

  async healthCheck(): Promise<{ status: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/health`)
      return this.handleResponse<{ status: string }>(response)
    } catch (error) {
      if (error instanceof TypeError && error.message.includes("fetch")) {
        throw new Error("Cannot connect to backend. Make sure the server is running on http://localhost:8000")
      }
      throw error
    }
  }

  async deleteAnalysis(analysisId: number): Promise<{ status: string; message: string }> {
    try {
      return await this.delete<{ status: string; message: string }>(`/api/analysis/${analysisId}`)
    } catch (error) {
      if (error instanceof TypeError && error.message.includes("fetch")) {
        throw new Error("Cannot connect to backend. Make sure the server is running on http://localhost:8000")
      }
      throw error
    }
  }

  async clearAllAnalyses(): Promise<{ status: string; message: string }> {
    try {
      return await this.delete<{ status: string; message: string }>("/api/analysis/")
    } catch (error) {
      if (error instanceof TypeError && error.message.includes("fetch")) {
        throw new Error("Cannot connect to backend. Make sure the server is running on http://localhost:8000")
      }
      throw error
    }
  }
}

export const api = new ApiService(API_BASE_URL)
