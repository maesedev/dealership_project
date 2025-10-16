"use client"

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireRoles?: string[]
}

export function ProtectedRoute({ children, requireRoles }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    // Si está cargando, no hacer nada
    if (isLoading) {
      return
    }

    // Si no está autenticado y no está en la página de login, redirigir a login
    if (!isAuthenticated && pathname !== '/login') {
      router.push('/login')
      return
    }

    // Si está autenticado pero está en login, redirigir a home
    if (isAuthenticated && pathname === '/login') {
      router.push('/')
      return
    }

    // Verificar roles si se especificaron
    if (isAuthenticated && requireRoles && requireRoles.length > 0 && user) {
      const hasRequiredRole = requireRoles.some(role => user.roles.includes(role))
      
      if (!hasRequiredRole) {
        console.warn('Usuario no tiene los permisos necesarios')
        // Podrías redirigir a una página de "no autorizado" o al home
        router.push('/')
      }
    }
  }, [isAuthenticated, isLoading, pathname, router, requireRoles, user])

  // Mostrar loader mientras se verifica la autenticación
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300">Cargando...</p>
        </div>
      </div>
    )
  }

  // Si no está autenticado y está en login, mostrar el contenido
  if (!isAuthenticated && pathname === '/login') {
    return <>{children}</>
  }

  // Si está autenticado, mostrar el contenido
  if (isAuthenticated) {
    return <>{children}</>
  }

  // En cualquier otro caso, no mostrar nada (se redirigirá)
  return null
}

