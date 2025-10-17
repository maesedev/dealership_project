"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/lib/auth-context"
import { api } from "@/lib/api-client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Clock, Calendar, MessageSquare, Plus, Activity, Loader2, AlertCircle, DollarSign, Target } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

// Interfaz basada en el schema del backend
interface DealerSession {
  id: string
  dealer_id: string
  start_time: string // ISO string
  end_time: string | null
  jackpot: number
  reik: number
  tips: number
  hourly_pay: number
  comment: string | null
  created_at: string
  updated_at: string
  is_active: boolean
  duration_hours: number | null
  total_earnings: number
}

interface DealerSessionProps {
  onSessionChange?: (hasActiveSession: boolean) => void
  onSessionEnd?: () => void
}

export function DealerSession({ onSessionChange, onSessionEnd }: DealerSessionProps) {
  const { user } = useAuth()
  // Estado para todas las sesiones (historial completo)
  const [sessions, setSessions] = useState<DealerSession[]>([])
  const [currentDurations, setCurrentDurations] = useState<Map<string, string>>(new Map())
  const [isLoading, setIsLoading] = useState(true)
  const [isStarting, setIsStarting] = useState(false)
  const [isEnding, setIsEnding] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [showEndModal, setShowEndModal] = useState<string | null>(null)
  const [endFormData, setEndFormData] = useState({
    reik: '',
    jackpot: ''
  })
  
  // Verificar si hay una sesión activa
  const hasActiveSession = sessions.some(session => session.is_active)

  // Función para calcular la duración desde el inicio hasta ahora
  const calculateDuration = (startTime: string): string => {
    const start = new Date(startTime)
    const now = new Date()
    const diffMs = now.getTime() - start.getTime()
    
    const hours = Math.floor(diffMs / (1000 * 60 * 60))
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
    
    return `${hours}h ${minutes}m`
  }

  // Cargar sesiones activas del usuario al montar el componente
  useEffect(() => {
    const loadActiveSessions = async () => {
      if (!user?.id) return
      
      try {
        setIsLoading(true)
        setError('')
        const response = await api.get(`/api/v1/sessions/active/user/${user.id}`)
        const activeSessions = response.sessions || []
        setSessions(activeSessions)
        
        // Notificar al componente padre sobre el estado de la sesión
        onSessionChange?.(activeSessions.length > 0)
      } catch (err: any) {
        console.error('Error al cargar sesiones activas:', err)
        setError(err.message || 'Error al cargar sesiones activas')
        onSessionChange?.(false)
      } finally {
        setIsLoading(false)
      }
    }

    loadActiveSessions()
  }, [user?.id, onSessionChange])

  // Actualizar duración cada minuto para todas las sesiones activas
  useEffect(() => {
    const activeSessions = sessions.filter(session => session.is_active)
    
    if (activeSessions.length > 0) {
      // Actualizar inmediatamente
      const newDurations = new Map<string, string>()
      activeSessions.forEach(session => {
        newDurations.set(session.id, calculateDuration(session.start_time))
      })
      setCurrentDurations(newDurations)
      
      // Actualizar cada minuto
      const interval = setInterval(() => {
        const updatedDurations = new Map<string, string>()
        activeSessions.forEach(session => {
          updatedDurations.set(session.id, calculateDuration(session.start_time))
        })
        setCurrentDurations(updatedDurations)
      }, 60000) // 60 segundos

      return () => clearInterval(interval)
    }
  }, [sessions])

  // Función para formatear fecha/hora (versión completa)
  const formatDateTime = (dateString: string): string => {
    const date = new Date(dateString)
    return date.toLocaleString('es-CO', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Función para formatear fecha/hora (versión corta para móviles)
  const formatDateTimeShort = (dateString: string): string => {
    const date = new Date(dateString)
    return date.toLocaleString('es-CO', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Handler para iniciar turno
  const handleStartShift = async () => {
    if (!user?.id) {
      setError('No se pudo identificar al usuario')
      return
    }

    try {
      setIsStarting(true)
      setError('')
      
      const now = new Date()
      const newSession = {
        dealer_id: user.id,
        start_time: now.toISOString(),
        jackpot: 0,
        reik: 0,
        tips: 0,
        hourly_pay: 0,
        comment: null
      }

      const response = await api.post('/api/v1/sessions', newSession)
      
      // Agregar la nueva sesión al principio del array (más reciente primero)
      const updatedSessions = [response, ...sessions]
      setSessions(updatedSessions)
      
      // Notificar al componente padre que ahora hay una sesión activa
      onSessionChange?.(true)
    } catch (err: any) {
      console.error('Error al iniciar turno:', err)
      setError(err.message || 'Error al iniciar el turno')
    } finally {
      setIsStarting(false)
    }
  }

  // Handler para abrir modal de terminar turno
  const handleOpenEndModal = (sessionId: string) => {
    setShowEndModal(sessionId)
    setEndFormData({ reik: '', jackpot: '' })
    setError('')
  }

  // Handler para cerrar modal de terminar turno
  const handleCloseEndModal = () => {
    setShowEndModal(null)
    setEndFormData({ reik: '', jackpot: '' })
    setError('')
  }

  // Handler para terminar turno
  const handleEndShift = async (sessionId: string) => {
    // Validar que los campos requeridos estén llenos
    if (!endFormData.reik.trim() || !endFormData.jackpot.trim()) {
      setError('Reik y Jackpot son campos obligatorios para terminar el turno')
      return
    }

    // Validar que sean números válidos
    const reik = parseFloat(endFormData.reik)
    const jackpot = parseFloat(endFormData.jackpot)
    
    if (isNaN(reik) || isNaN(jackpot)) {
      setError('Reik y Jackpot deben ser números válidos')
      return
    }

    try {
      setIsEnding(sessionId)
      setError('')
      
      // Actualizar la sesión con los valores de reik y jackpot
      await api.put(`/api/v1/sessions/${sessionId}`, {
        reik: reik,
        jackpot: jackpot
      })
      
      // Terminar la sesión
      await api.post(`/api/v1/sessions/${sessionId}/end`)
      
      // Actualizar la sesión en el estado local
      const updatedSessions = sessions.map(session => {
        if (session.id === sessionId && session.is_active) {
          const now = new Date()
          return {
            ...session,
            end_time: now.toISOString(),
            is_active: false,
            updated_at: now.toISOString(),
            duration_hours: (now.getTime() - new Date(session.start_time).getTime()) / (1000 * 60 * 60),
            reik: reik,
            jackpot: jackpot
          }
        }
        return session
      })
      setSessions(updatedSessions)
      
      // Verificar si quedan sesiones activas
      const hasActive = updatedSessions.some(session => session.is_active)
      onSessionChange?.(hasActive)

      // Notificar que se terminó la sesión para limpiar memoria
      onSessionEnd?.()

      // Cerrar modal
      handleCloseEndModal()
    } catch (err: any) {
      console.error('Error al terminar turno:', err)
      setError(err.message || 'Error al terminar el turno')
    } finally {
      setIsEnding(null)
    }
  }

  // Handler para agregar comentarios (por ahora solo simula)
  const handleAddComment = () => {
    // TODO: Implementar funcionalidad de agregar comentarios
    console.log("Agregar comentario")
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-8">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Error */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        </div>
      )}

      {/* Botón para iniciar turno */}
      <div className="flex justify-center px-2">
        <Button
          onClick={handleStartShift}
          disabled={hasActiveSession || isStarting}
          size="lg"
          className="w-full sm:w-auto bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-semibold py-4 sm:py-6 px-6 sm:px-8 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
        >
          {isStarting ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Iniciando...
            </>
          ) : (
            <>
              <Plus className="w-5 h-5 mr-2" />
              Iniciar Turno
            </>
          )}
        </Button>
      </div>

      {/* Todas las sesiones (más reciente primero) */}
      {sessions.map((session) => (
        <Card key={session.id} className="shadow-xl border-0 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm mx-2 sm:mx-0">
          <CardHeader className={`${session.is_active ? 'bg-gradient-to-r from-purple-500 to-pink-600' : 'bg-gradient-to-r from-gray-500 to-gray-600'} text-white rounded-t-lg py-4 px-4 sm:px-6`}>
            <CardTitle className="text-lg sm:text-xl font-semibold flex items-center gap-2">
              <Activity className="w-5 h-5 sm:w-6 sm:h-6" />
              {session.is_active ? "Turno Actual" : "Turno Finalizado"}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 sm:p-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 sm:gap-6">
              {/* Hora de inicio */}
              <div className="space-y-2 bg-gray-50 dark:bg-gray-700/50 p-3 rounded-lg">
                <div className="flex items-center gap-2 text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">
                  <Clock className="w-4 h-4" />
                  Hora de Inicio
                </div>
                <div className="text-sm sm:text-lg font-semibold text-gray-800 dark:text-white break-words">
                  <span className="hidden sm:inline">{formatDateTime(session.start_time)}</span>
                  <span className="sm:hidden">{formatDateTimeShort(session.start_time)}</span>
                </div>
              </div>

              {/* Hora de fin */}
              <div className="space-y-2 bg-gray-50 dark:bg-gray-700/50 p-3 rounded-lg">
                <div className="flex items-center gap-2 text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">
                  <Calendar className="w-4 h-4" />
                  Hora de Fin
                </div>
                <div className="text-sm sm:text-lg font-semibold text-gray-800 dark:text-white break-words">
                  {session.end_time ? (
                    <>
                      <span className="hidden sm:inline">{formatDateTime(session.end_time)}</span>
                      <span className="sm:hidden">{formatDateTimeShort(session.end_time)}</span>
                    </>
                  ) : "---"}
                </div>
              </div>

              {/* Comentarios del turno */}
              <div className="space-y-2 bg-gray-50 dark:bg-gray-700/50 p-3 rounded-lg sm:col-span-2 lg:col-span-1">
                <div className="flex items-center gap-2 text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">
                  <MessageSquare className="w-4 h-4" />
                  Comentarios
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-sm sm:text-lg font-semibold text-gray-800 dark:text-white truncate flex-1">
                    {session.comment || "Sin comentarios"}
                  </div>
                  <Button
                    onClick={handleAddComment}
                    variant="outline"
                    size="sm"
                    className="text-blue-600 border-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 shrink-0 h-8 w-8 p-0"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Duración */}
              <div className="space-y-2 bg-gray-50 dark:bg-gray-700/50 p-3 rounded-lg">
                <div className="flex items-center gap-2 text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">
                  <Clock className="w-4 h-4" />
                  Duración
                </div>
                <div className="text-sm sm:text-lg font-semibold text-gray-800 dark:text-white">
                  {session.is_active ? (currentDurations.get(session.id) || "0h 0m") : 
                    session.duration_hours ? 
                    `${Math.floor(session.duration_hours)}h ${Math.floor((session.duration_hours % 1) * 60)}m` : 
                    "---"}
                </div>
              </div>

              {/* Estado */}
              <div className="space-y-2 bg-gray-50 dark:bg-gray-700/50 p-3 rounded-lg">
                <div className="flex items-center gap-2 text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">
                  <Activity className="w-4 h-4" />
                  Estado
                </div>
                <div>
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs sm:text-sm font-semibold ${
                      session.is_active
                        ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                        : "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200"
                    }`}
                  >
                    {session.is_active ? "Activo" : "Terminado"}
                  </span>
                </div>
              </div>
            </div>

            {/* Botón Terminar Turno */}
            {session.is_active && (
              <div className="flex justify-stretch sm:justify-end mt-4 sm:mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                <Button
                  onClick={() => handleOpenEndModal(session.id)}
                  disabled={isEnding === session.id}
                  size="lg"
                  className="w-full sm:w-auto bg-gradient-to-r from-red-500 to-rose-600 hover:from-red-600 hover:to-rose-700 text-white font-semibold py-3 px-6 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Terminar Turno
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      ))}

      {/* Modal para terminar turno */}
      {showEndModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="text-red-600 dark:text-red-400">
                Terminar Turno
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Para terminar el turno, completa los siguientes campos obligatorios:
                </p>

                {error && (
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded p-3 text-sm text-red-800 dark:text-red-200">
                    {error}
                  </div>
                )}

                <div className="space-y-4">
                  <div>
                    <Label htmlFor="reik" className="flex items-center gap-2">
                      <DollarSign className="h-4 w-4" />
                      Reik *
                    </Label>
                    <Input
                      id="reik"
                      type="number"
                      step="1000"
                      placeholder="Ingresa el valor del reik"
                      value={endFormData.reik}
                      onChange={(e) => setEndFormData({ ...endFormData, reik: e.target.value })}
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="jackpot" className="flex items-center gap-2">
                      <Target className="h-4 w-4" />
                      Jackpot *
                    </Label>
                    <Input
                      id="jackpot"
                      type="number"
                      step="1000"
                      placeholder="Ingresa el valor del jackpot"
                      value={endFormData.jackpot}
                      onChange={(e) => setEndFormData({ ...endFormData, jackpot: e.target.value })}
                      className="mt-1"
                    />
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    onClick={handleCloseEndModal}
                    className="flex-1"
                    disabled={isEnding === showEndModal}
                  >
                    Cancelar
                  </Button>
                  <Button
                    onClick={() => handleEndShift(showEndModal)}
                    disabled={isEnding === showEndModal || !endFormData.reik.trim() || !endFormData.jackpot.trim()}
                    className="flex-1 bg-gradient-to-r from-red-500 to-rose-600 hover:from-red-600 hover:to-rose-700"
                  >
                    {isEnding === showEndModal ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Terminando...
                      </>
                    ) : (
                      'Terminar Turno'
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

