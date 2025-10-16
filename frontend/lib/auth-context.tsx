"use client"

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'

// Tipos de datos
interface User {
  id: string
  username: string
  name: string
  roles: string[]
  is_active: boolean
  created_at: string
  updated_at: string
  security?: {
    failed_attempts: number
  }
}

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
}

// Crear el contexto
const AuthContext = createContext<AuthContextType | undefined>(undefined)

// URL del backend (ajusta según tu configuración)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  // Función para guardar el token en localStorage
  const saveToken = (newToken: string) => {
    localStorage.setItem('auth_token', newToken)
    setToken(newToken)
  }

  // Función para limpiar el token
  const clearToken = () => {
    localStorage.removeItem('auth_token')
    setToken(null)
  }

  // Función para obtener información del usuario actual
  const fetchCurrentUser = useCallback(async (authToken: string) => {
    try {
      console.log('🔍 [DEBUG] fetchCurrentUser iniciado con token:', authToken.substring(0, 20) + '...')
      console.log('🔍 [DEBUG] URL del endpoint:', `${API_BASE_URL}/api/v1/auth/me`)
      
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      })

      console.log('🔍 [DEBUG] Respuesta del servidor:', {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.log('🔍 [DEBUG] Error response body:', errorText)
        throw new Error('No se pudo obtener información del usuario')
      }

      const userData = await response.json()
      console.log('🔍 [DEBUG] Datos del usuario recibidos:', userData)
      setUser(userData.user)
      console.log('🔍 [DEBUG] Usuario seteado en estado:', userData.user)
      return userData.user
    } catch (error) {
      console.error('🔍 [DEBUG] Error al obtener usuario:', error)
      throw error
    }
  }, [])

  // Función de login
  const login = async (username: string, password: string) => {
    try {
      setIsLoading(true)
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Error al iniciar sesión')
      }

      const data = await response.json()
      
      // Guardar token
      saveToken(data.access_token)
      
      // Guardar información del usuario
      setUser(data.user)

      // Configurar renovación automática del token
      scheduleTokenRefresh(data.expires_in)

      // Redirigir a la página principal
      router.push('/')
    } catch (error) {
      console.error('Error en login:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  // Función de logout
  const logout = useCallback(() => {
    clearToken()
    setUser(null)
    router.push('/login')
  }, [router])

  // Función para refrescar el token
  const refreshToken = useCallback(async () => {
    const currentToken = token || localStorage.getItem('auth_token')
    
    if (!currentToken) {
      logout()
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${currentToken}`
        }
      })

      if (!response.ok) {
        throw new Error('No se pudo renovar el token')
      }

      const data = await response.json()
      
      // Actualizar token
      saveToken(data.access_token)
      
      // Actualizar información del usuario
      setUser(data.user)

      // Programar la próxima renovación
      scheduleTokenRefresh(data.expires_in)
    } catch (error) {
      console.error('Error al renovar token:', error)
      logout()
    }
  }, [token, logout])

  // Programar renovación automática del token (5 minutos antes de expirar)
  const scheduleTokenRefresh = (expiresIn: number) => {
    // Renovar el token 5 minutos antes de que expire
    const refreshTime = (expiresIn - 300) * 1000 // Convertir a milisegundos
    
    if (refreshTime > 0) {
      setTimeout(() => {
        refreshToken()
      }, refreshTime)
    }
  }

  // Verificar token al cargar la aplicación
  useEffect(() => {
    const initAuth = async () => {
      try {
        console.log('🚀 [DEBUG] Iniciando autenticación...')
        const storedToken = localStorage.getItem('auth_token')
        console.log('🚀 [DEBUG] Token encontrado en localStorage:', storedToken ? 'SÍ' : 'NO')
        console.log('🚀 [DEBUG] Token (primeros 20 chars):', storedToken ? storedToken.substring(0, 20) + '...' : 'null')
        
        if (storedToken) {
          console.log('🚀 [DEBUG] Token existe, seteando en estado...')
          setToken(storedToken)
          
          // Intentar obtener información del usuario
          try {
            console.log('🚀 [DEBUG] Intentando obtener datos del usuario...')
            await fetchCurrentUser(storedToken)
            console.log('🚀 [DEBUG] Usuario obtenido exitosamente, programando renovación...')
            // Si el token es válido, programar renovación
            // Los tokens del backend expiran en 30 minutos (1800 segundos)
            scheduleTokenRefresh(1800)
          } catch (error) {
            // Token inválido o expirado
            console.error('🚀 [DEBUG] Token inválido, limpiando y redirigiendo:', error)
            clearToken()
            router.push('/login')
          }
        } else {
          console.log('🚀 [DEBUG] No hay token, usuario no autenticado')
        }
      } catch (error) {
        console.error('🚀 [DEBUG] Error general al inicializar autenticación:', error)
      } finally {
        console.log('🚀 [DEBUG] Finalizando carga, isLoading = false')
        setIsLoading(false)
      }
    }

    initAuth()
  }, [fetchCurrentUser, router])

  // Interceptor global para manejar errores 401 (no autorizado)
  useEffect(() => {
    const handleUnauthorized = (event: CustomEvent) => {
      console.warn('Sesión no autorizada, cerrando sesión...')
      logout()
    }

    window.addEventListener('unauthorized' as any, handleUnauthorized)
    return () => {
      window.removeEventListener('unauthorized' as any, handleUnauthorized)
    }
  }, [logout])

  // Debug del estado actual
  console.log('🔍 [DEBUG] Estado actual del AuthContext:', {
    user: user ? { id: user.id, name: user.name, username: user.username, roles: user.roles } : null,
    token: token ? token.substring(0, 20) + '...' : null,
    isLoading,
    isAuthenticated: !!user && !!token
  })

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated: !!user && !!token,
    login,
    logout,
    refreshToken
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

// Hook personalizado para usar el contexto
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth debe ser usado dentro de un AuthProvider')
  }
  return context
}

