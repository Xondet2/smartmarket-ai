import { api } from "./api"

export interface User {
  id: number
  email: string
  username: string
  full_name: string
  is_active: boolean
  is_admin: boolean
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
  full_name: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
}

const TOKEN_KEY = "smartmarket_token"

export const authService = {
  async register(data: RegisterData): Promise<User> {
    const response = await api.post("/api/auth/register", data)
    return response
  },

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await api.post("/api/auth/login", credentials)
    if (response.access_token) {
      this.setToken(response.access_token)
    }
    return response
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get("/api/auth/me")
    return response
  },

  async updateProfile(full_name: string): Promise<User> {
    const response = await api.put("/api/auth/me", { full_name })
    return response
  },

  logout() {
    this.removeToken()
    window.location.href = "/login"
  },

  setToken(token: string) {
    localStorage.setItem(TOKEN_KEY, token)
  },

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY)
  },

  removeToken() {
    localStorage.removeItem(TOKEN_KEY)
  },

  isAuthenticated(): boolean {
    return !!this.getToken()
  },
}
