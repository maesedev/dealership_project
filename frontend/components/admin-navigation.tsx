"use client"

import { useAuth } from '@/lib/auth-context'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Users, Settings, FileText } from 'lucide-react'
import { useRouter } from 'next/navigation'

export function AdminNavigation() {
  const { user } = useAuth()
  const router = useRouter()

  // Solo mostrar para ADMIN y MANAGER
  if (!user || !user.roles || (!user.roles.includes('ADMIN') && !user.roles.includes('MANAGER'))) {
    return null
  }

  return (
    <Card className="shadow-lg border-0 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 backdrop-blur-sm">
      <CardContent className="p-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-r from-purple-500 to-pink-600 p-2 rounded-full">
              <Settings className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="font-semibold text-gray-800 dark:text-white">
                Panel de Administración
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Gestiona el sistema
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => router.push('/daily-report')}
              variant="outline"
              size="sm"
              className="flex items-center gap-2 border-purple-300 text-purple-700 dark:text-purple-300 hover:bg-purple-50 dark:hover:bg-purple-900/20"
            >
              <FileText className="h-4 w-4" />
              Reporte Diario
            </Button>
            <Button
              onClick={() => router.push('/admin/users')}
              variant="outline"
              size="sm"
              className="flex items-center gap-2 border-purple-300 text-purple-700 dark:text-purple-300 hover:bg-purple-50 dark:hover:bg-purple-900/20"
            >
              <Users className="h-4 w-4" />
              Usuarios
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

