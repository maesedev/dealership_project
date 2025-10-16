"use client"

import { useEffect, useState } from 'react'
import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  UserPlus,
  Edit2,
  Trash2,
  CheckCircle,
  XCircle,
  Shield,
  Search,
  Loader2,
  AlertCircle,
  ArrowLeft,
} from 'lucide-react'

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

export default function UsersAdminPage() {
  const { user: currentUser, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const [users, setUsers] = useState<User[]>([])
  const [filteredUsers, setFilteredUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [error, setError] = useState('')

  // Verificar permisos
  useEffect(() => {
    if (!authLoading && currentUser) {
      const hasPermission = currentUser.roles.includes('ADMIN') || currentUser.roles.includes('MANAGER')
      if (!hasPermission) {
        router.push('/')
      }
    }
  }, [currentUser, authLoading, router])

  // Cargar usuarios
  const loadUsers = async () => {
    try {
      setIsLoading(true)
      setError('')
      const response = await api.get('/api/v1/users?limit=1000')
      setUsers(response.users || response)
      setFilteredUsers(response.users || response)
    } catch (err: any) {
      setError(err.message || 'Error al cargar usuarios')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (currentUser?.roles.includes('ADMIN') || currentUser?.roles.includes('MANAGER')) {
      loadUsers()
    }
  }, [currentUser])

  // Filtrar usuarios
  useEffect(() => {
    if (searchTerm) {
      const filtered = users.filter(
        (u) =>
          u.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          u.username?.toLowerCase().includes(searchTerm.toLowerCase())
      )
      setFilteredUsers(filtered)
    } else {
      setFilteredUsers(users)
    }
  }, [searchTerm, users])

  // Activar usuario
  const activateUser = async (userId: string) => {
    try {
      await api.post(`/api/v1/users/${userId}/activate`)
      await loadUsers()
    } catch (err: any) {
      alert('Error: ' + err.message)
    }
  }

  // Desactivar usuario
  const deactivateUser = async (userId: string) => {
    try {
      await api.post(`/api/v1/users/${userId}/deactivate`)
      await loadUsers()
    } catch (err: any) {
      alert('Error: ' + err.message)
    }
  }

  // Eliminar usuario
  const deleteUser = async (userId: string, userName: string) => {
    if (!confirm(`¿Estás seguro de eliminar al usuario "${userName}"?`)) return

    try {
      await api.delete(`/api/v1/users/${userId}`)
      await loadUsers()
    } catch (err: any) {
      alert('Error: ' + err.message)
    }
  }

  const getRoleBadgeColor = (roles: string[]) => {
    if (roles.includes('ADMIN')) return 'bg-red-500 text-white'
    if (roles.includes('MANAGER')) return 'bg-purple-500 text-white'
    if (roles.includes('DEALER')) return 'bg-blue-500 text-white'
    return 'bg-gray-500 text-white'
  }

  const isAdmin = currentUser?.roles.includes('ADMIN')

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    )
  }

  if (!currentUser?.roles.includes('ADMIN') && !currentUser?.roles.includes('MANAGER')) {
    return null
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/')}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Volver
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-gray-800 dark:text-white">
                Administración de Usuarios
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Gestiona los usuarios del sistema
              </p>
            </div>
          </div>
          <Button
            onClick={() => setShowCreateModal(true)}
            className="bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700"
          >
            <UserPlus className="h-4 w-4 mr-2" />
            Crear Usuario
          </Button>
        </div>

        {/* Buscador */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Search className="h-5 w-5 text-gray-400" />
              <Input
                placeholder="Buscar por nombre o usuario..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="flex-1"
              />
            </div>
          </CardContent>
        </Card>

        {/* Error */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <p className="text-red-800 dark:text-red-200">{error}</p>
            </div>
          </div>
        )}

        {/* Lista de Usuarios */}
        <Card>
          <CardHeader>
            <CardTitle>
              Usuarios ({filteredUsers.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Nombre</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Usuario</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Roles</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Estado</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((user) => (
                    <tr
                      key={user.id}
                      className="border-b border-gray-100 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700"
                    >
                      <td className="px-4 py-3">
                        <div className="font-medium">{user.name}</div>
                        <div className="text-xs text-gray-500">
                          ID: {user.id.substring(0, 8)}...
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="font-mono text-sm">
                          {user.username || '-'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {user.roles.map((role) => (
                            <span
                              key={role}
                              className={`px-2 py-1 rounded text-xs font-semibold ${getRoleBadgeColor(
                                [role]
                              )}`}
                            >
                              {role}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {user.is_active ? (
                          <span className="flex items-center gap-1 text-green-600 dark:text-green-400 text-sm">
                            <CheckCircle className="h-4 w-4" />
                            Activo
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-red-600 dark:text-red-400 text-sm">
                            <XCircle className="h-4 w-4" />
                            Inactivo
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setEditingUser(user)}
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          {isAdmin && (
                            <>
                              {user.is_active ? (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => deactivateUser(user.id)}
                                  className="text-orange-600"
                                >
                                  <XCircle className="h-4 w-4" />
                                </Button>
                              ) : (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => activateUser(user.id)}
                                  className="text-green-600"
                                >
                                  <CheckCircle className="h-4 w-4" />
                                </Button>
                              )}
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => deleteUser(user.id, user.name)}
                                className="text-red-600"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Modal Crear Usuario */}
      {showCreateModal && (
        <CreateUserModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false)
            loadUsers()
          }}
          isAdmin={isAdmin}
        />
      )}

      {/* Modal Editar Usuario */}
      {editingUser && (
        <EditUserModal
          user={editingUser}
          onClose={() => setEditingUser(null)}
          onSuccess={() => {
            setEditingUser(null)
            loadUsers()
          }}
          isAdmin={isAdmin}
        />
      )}
    </div>
  )
}

// Modal Crear Usuario
function CreateUserModal({
  onClose,
  onSuccess,
  isAdmin,
}: {
  onClose: () => void
  onSuccess: () => void
  isAdmin: boolean
}) {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    name: '',
    roles: ['USER'],
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      await api.post('/api/v1/users/create', formData)
      onSuccess()
    } catch (err: any) {
      setError(err.message || 'Error al crear usuario')
    } finally {
      setIsLoading(false)
    }
  }

  const toggleRole = (role: string) => {
    if (formData.roles.includes(role)) {
      setFormData({ ...formData, roles: formData.roles.filter((r) => r !== role) })
    } else {
      setFormData({ ...formData, roles: [...formData.roles, role] })
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Crear Nuevo Usuario</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 rounded p-3 text-sm text-red-800 dark:text-red-200">
                {error}
              </div>
            )}

            <div>
              <Label>Nombre Completo</Label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>

            <div>
              <Label>Usuario</Label>
              <Input
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              />
            </div>

            <div>
              <Label>Contraseña</Label>
              <Input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              />
            </div>

            <div>
              <Label className="mb-2 block">Roles</Label>
              <div className="space-y-2">
                {['USER', 'DEALER', 'MANAGER', 'ADMIN'].map((role) => (
                  <label key={role} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.roles.includes(role)}
                      onChange={() => toggleRole(role)}
                      disabled={!isAdmin && (role === 'ADMIN' || role === 'MANAGER')}
                      className="rounded"
                    />
                    <span className="text-sm">{role}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={onClose} className="flex-1">
                Cancelar
              </Button>
              <Button type="submit" disabled={isLoading} className="flex-1">
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Crear'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

// Modal Editar Usuario
function EditUserModal({
  user,
  onClose,
  onSuccess,
  isAdmin,
}: {
  user: User
  onClose: () => void
  onSuccess: () => void
  isAdmin: boolean
}) {
  const [formData, setFormData] = useState({
    name: user.name,
    roles: user.roles,
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      await api.put(`/api/v1/users/${user.id}`, { name: formData.name })
      if (isAdmin && JSON.stringify(formData.roles) !== JSON.stringify(user.roles)) {
        await api.put(`/api/v1/users/${user.id}/roles`, { roles: formData.roles })
      }
      onSuccess()
    } catch (err: any) {
      setError(err.message || 'Error al actualizar usuario')
    } finally {
      setIsLoading(false)
    }
  }

  const toggleRole = (role: string) => {
    if (formData.roles.includes(role)) {
      setFormData({ ...formData, roles: formData.roles.filter((r) => r !== role) })
    } else {
      setFormData({ ...formData, roles: [...formData.roles, role] })
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Editar Usuario</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 rounded p-3 text-sm text-red-800 dark:text-red-200">
                {error}
              </div>
            )}

            <div>
              <Label>Nombre Completo</Label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>

            <div>
              <Label>Usuario</Label>
              <Input value={user.username || '-'} disabled />
            </div>

            {isAdmin && (
              <div>
                <Label className="mb-2 block">Roles</Label>
                <div className="space-y-2">
                  {['USER', 'DEALER', 'MANAGER', 'ADMIN'].map((role) => (
                    <label key={role} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.roles.includes(role)}
                        onChange={() => toggleRole(role)}
                        className="rounded"
                      />
                      <span className="text-sm">{role}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={onClose} className="flex-1">
                Cancelar
              </Button>
              <Button type="submit" disabled={isLoading} className="flex-1">
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Guardar'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

