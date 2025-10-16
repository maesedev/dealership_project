"use client"

import { useAuth } from '@/lib/auth-context'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { LogOut, User, Shield } from 'lucide-react'

export function UserMenu() {
  const { user, logout } = useAuth()

  if (!user) return null

  const getRoleBadge = (roles: string[]) => {
    if (roles.includes('ADMIN')) return { label: 'Admin', color: 'bg-red-500' }
    if (roles.includes('MANAGER')) return { label: 'Manager', color: 'bg-purple-500' }
    if (roles.includes('DEALER')) return { label: 'Dealer', color: 'bg-blue-500' }
    return { label: 'Usuario', color: 'bg-gray-500' }
  }

  const badge = getRoleBadge(user.roles)

  return (
    <Card className="shadow-lg border-0 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm">
      <CardContent className="p-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-r from-blue-500 to-indigo-600 p-2 rounded-full">
              <User className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="font-semibold text-gray-800 dark:text-white">
                {user.name}
              </p>
              <div className="flex items-center gap-2">
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  @{user.username}
                </p>
                <span className={`${badge.color} text-white text-xs px-2 py-0.5 rounded-full flex items-center gap-1`}>
                  <Shield className="h-3 w-3" />
                  {badge.label}
                </span>
              </div>
            </div>
          </div>
          <Button
            onClick={logout}
            variant="outline"
            size="sm"
            className="text-red-600 border-red-300 hover:bg-red-50 dark:hover:bg-red-900/20"
          >
            <LogOut className="h-4 w-4 mr-1" />
            Salir
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

