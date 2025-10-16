/**
 * Cliente HTTP para comunicarse con la API del backend
 * Incluye manejo automático de autenticación y errores
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface RequestOptions extends RequestInit {
  requireAuth?: boolean
}

/**
 * Realiza una petición HTTP al backend con manejo de errores y autenticación
 */
export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { requireAuth = true, ...fetchOptions } = options

  // Construir headers
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...fetchOptions.headers,
  }

  // Agregar token de autenticación si se requiere
  if (requireAuth && typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_token')
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  // Realizar petición
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...fetchOptions,
      headers,
    })

    // Manejar errores HTTP
    if (!response.ok) {
      // Si es 401 (no autorizado), disparar evento para que el AuthContext lo maneje
      if (response.status === 401) {
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('unauthorized'))
        }
        throw new Error('Sesión expirada. Por favor, inicia sesión nuevamente.')
      }

      // Intentar obtener mensaje de error del servidor
      let errorMessage = `Error ${response.status}: ${response.statusText}`
      try {
        const errorData = await response.json()
        errorMessage = errorData.detail || errorData.message || errorMessage
      } catch {
        // Si no se puede parsear el error, usar el mensaje por defecto
      }

      throw new Error(errorMessage)
    }

    // Intentar parsear respuesta como JSON
    const contentType = response.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {
      return await response.json()
    }

    // Si no es JSON, devolver texto
    return (await response.text()) as any
  } catch (error) {
    // Re-lanzar errores para que el componente los maneje
    if (error instanceof Error) {
      throw error
    }
    throw new Error('Error de red. Por favor, verifica tu conexión.')
  }
}

/**
 * Métodos auxiliares para diferentes tipos de peticiones HTTP
 */
export const api = {
  get: <T = any>(endpoint: string, options?: RequestOptions) =>
    apiRequest<T>(endpoint, { ...options, method: 'GET' }),

  post: <T = any>(endpoint: string, data?: any, options?: RequestOptions) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }),

  put: <T = any>(endpoint: string, data?: any, options?: RequestOptions) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }),

  delete: <T = any>(endpoint: string, options?: RequestOptions) =>
    apiRequest<T>(endpoint, { ...options, method: 'DELETE' }),
}

