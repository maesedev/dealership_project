"use client"

import React, { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import { api } from "@/lib/api-client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { UserMenu } from "@/components/user-menu"
import {
  TrendingUp,
  TrendingDown,
  Calculator,
  RefreshCw,
  AlertCircle,
  ArrowLeft,
  Sun,
  Moon,
  ChevronDown,
  ChevronUp,
  Edit2,
} from "lucide-react"
import { useTheme } from "next-themes"

interface DailyReportData {
  id: string
  date: string
  reik: number
  jackpot: number
  ganancias: number
  gastos: number
  sessions: string[]
  jackpot_wins: Array<{ jackpot_win_id: string; sum: number }>
  bonos: Array<{ bono_id: string; sum: number }>
  comment: string | null
  created_at: string
  updated_at: string
  total_income: number
  is_profitable: boolean
  profit_margin: number
}

interface SessionData {
  id: string
  dealer_id: string
  start_time: string
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
  dealer_name?: string // Added for displaying dealer name
}

interface JackpotData {
  id: string
  user_id: string
  session_id: string
  value: number
  winner_hand: string
  comment: string | null
  created_at: string
  updated_at: string
  user_name?: string
}

interface BonoData {
  id: string
  user_id: string
  session_id: string
  value: number
  comment: string | null
  created_at: string
  updated_at: string
  user_name?: string
}

export default function DailyReportPage() {
  const { theme, setTheme } = useTheme()
  const { user } = useAuth()
  const router = useRouter()
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  )
  const [reportData, setReportData] = useState<DailyReportData | null>(null)
  const [sessionsData, setSessionsData] = useState<SessionData[]>([])
  const [jackpotsData, setJackpotsData] = useState<JackpotData[]>([])
  const [bonosData, setBonosData] = useState<BonoData[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null)
  const [newHourlyPay, setNewHourlyPay] = useState<number>(0)
  const [isSessionsExpanded, setIsSessionsExpanded] = useState<boolean>(true)
  const [isJackpotsExpanded, setIsJackpotsExpanded] = useState<boolean>(false)
  const [isBonosExpanded, setIsBonosExpanded] = useState<boolean>(false)
  const [editingSessionData, setEditingSessionData] = useState<string | null>(null)
  const [editFormData, setEditFormData] = useState({ reik: 0, jackpot: 0, tips: 0 })

  // Verificar permisos
  useEffect(() => {
    if (user && !user.roles?.includes("MANAGER") && !user.roles?.includes("ADMIN")) {
      router.push("/")
    }
  }, [user, router])

  // Cargar reporte cuando cambia la fecha
  useEffect(() => {
    if (user && (user.roles?.includes("MANAGER") || user.roles?.includes("ADMIN"))) {
      loadReport()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate, user])

  const loadReport = async () => {
    setLoading(true)
    setError(null)
    try {
      // Obtener el reporte del día
      const report = await api.get<DailyReportData>(
        `/api/v1/daily-reports/date/${selectedDate}`
      )
      setReportData(report)

      // Cargar datos de las sesiones
      if (report.sessions && report.sessions.length > 0) {
        console.log("Cargando sesiones:", report.sessions)
        const sessionsPromises = report.sessions.map(async (sessionId) => {
          try {
            console.log("Cargando sesión:", sessionId)
            const sessionData = await api.get<SessionData>(`/api/v1/sessions/${sessionId}`)
            console.log("Sesión cargada:", sessionData)
            
            // Cargar nombre del dealer
            try {
              console.log("Cargando dealer para sesión:", sessionData.id, "dealer_id:", sessionData.dealer_id)
              const dealerData = await api.get<{ name: string }>(
                `/api/v1/users/${sessionData.dealer_id}`
              )
              console.log("Dealer data recibida:", dealerData)
              sessionData.dealer_name = dealerData.name
            } catch (err) {
              console.error("Error al cargar dealer:", err)
              sessionData.dealer_name = "Dealer desconocido"
            }
            return sessionData
          } catch (err) {
            console.error("Error al cargar sesión:", err)
            return null
          }
        })
        const sessions = (await Promise.all(sessionsPromises)).filter(
          (s) => s !== null
        ) as SessionData[]
        console.log("Sesiones finales:", sessions)
        setSessionsData(sessions)
      } else {
        setSessionsData([])
      }

      // Cargar datos completos de jackpots
      if (report.jackpot_wins && report.jackpot_wins.length > 0) {
        const jackpotsPromises = report.jackpot_wins.map(async (jackpot) => {
          try {
            const jackpotData = await api.get<JackpotData>(
              `/api/v1/jackpot-prices/${jackpot.jackpot_win_id}`
            )
            // Cargar nombre del usuario
            try {
              const userData = await api.get<{ name: string }>(
                `/api/v1/users/${jackpotData.user_id}`
              )
              jackpotData.user_name = userData.name
            } catch (err) {
              console.error("Error al cargar usuario:", err)
              jackpotData.user_name = "Usuario desconocido"
            }
            return jackpotData
          } catch (err) {
            console.error("Error al cargar jackpot:", err)
            return null
          }
        })
        const jackpots = (await Promise.all(jackpotsPromises)).filter(
          (j) => j !== null
        ) as JackpotData[]
        setJackpotsData(jackpots)
      } else {
        setJackpotsData([])
      }

      // Cargar datos completos de bonos
      if (report.bonos && report.bonos.length > 0) {
        const bonosPromises = report.bonos.map(async (bono) => {
          try {
            const bonoData = await api.get<BonoData>(
              `/api/v1/bonos/${bono.bono_id}`
            )
            // Cargar nombre del usuario
            try {
              const userData = await api.get<{ name: string }>(
                `/api/v1/users/${bonoData.user_id}`
              )
              bonoData.user_name = userData.name
            } catch (err) {
              console.error("Error al cargar usuario:", err)
              bonoData.user_name = "Usuario desconocido"
            }
            return bonoData
          } catch (err) {
            console.error("Error al cargar bono:", err)
            return null
          }
        })
        const bonos = (await Promise.all(bonosPromises)).filter(
          (b) => b !== null
        ) as BonoData[]
        setBonosData(bonos)
      } else {
        setBonosData([])
      }
    } catch (err: unknown) {
      console.error("Error al cargar reporte:", err)
      const errorMessage = err instanceof Error ? err.message : "Error al cargar el reporte"
      setError(errorMessage)
      setReportData(null)
      setSessionsData([])
      setJackpotsData([])
      setBonosData([])
    } finally {
      setLoading(false)
    }
  }

  const updateSessionHourlyPay = async (sessionId: string) => {
    try {
      await api.put(`/api/v1/sessions/${sessionId}`, {
        hourly_pay: newHourlyPay,
      })
      // Recargar el reporte para reflejar los cambios
      await loadReport()
      setEditingSessionId(null)
      setNewHourlyPay(0)
    } catch (err: unknown) {
      console.error("Error al actualizar sesión:", err)
      const errorMessage = err instanceof Error ? err.message : "Error desconocido"
      alert("Error al actualizar el valor por hora: " + errorMessage)
    }
  }

  const startEditingSession = (session: SessionData) => {
    setEditingSessionData(session.id)
    setEditFormData({
      reik: session.reik,
      jackpot: session.jackpot,
      tips: session.tips,
    })
  }

  const cancelEditingSession = () => {
    setEditingSessionData(null)
    setEditFormData({ reik: 0, jackpot: 0, tips: 0 })
  }

  const updateSessionData = async (sessionId: string) => {
    try {
      await api.put(`/api/v1/sessions/${sessionId}`, editFormData)
      // Recargar el reporte para reflejar los cambios
      await loadReport()
      setEditingSessionData(null)
      setEditFormData({ reik: 0, jackpot: 0, tips: 0 })
    } catch (err: unknown) {
      console.error("Error al actualizar sesión:", err)
      const errorMessage = err instanceof Error ? err.message : "Error desconocido"
      alert("Error al actualizar la sesión: " + errorMessage)
    }
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency: "COP",
      minimumFractionDigits: 0,
    }).format(value)
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString("es-CO", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleString("es-CO", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    })
  }

  // Si no es Manager o Admin, no mostrar nada (ya redirige)
  if (!user || (!user.roles?.includes("MANAGER") && !user.roles?.includes("ADMIN"))) {
    return null
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-2 sm:p-4">
      <div className="max-w-full sm:max-w-[90vw] md:max-w-[85vw] lg:max-w-[80vw] xl:max-w-[75vw] mx-auto space-y-4 sm:space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between gap-2">
          <div className="text-center flex-1">
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-800 dark:text-white mb-1 sm:mb-2">
              📊 Reporte Diario
            </h1>
            <p className="text-xs sm:text-sm md:text-base text-gray-600 dark:text-gray-300">
              Análisis de ingresos, egresos y sesiones del día
            </p>
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="ml-2 shrink-0"
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
        </div>

        {/* User Menu */}
        <UserMenu />

        {/* Botón de regreso */}
        <Button
          onClick={() => router.push("/")}
          variant="outline"
          className="flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver a Ficha de Jugadores
        </Button>

        {/* Selector de fecha */}
        <Card className="shadow-xl border-0 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm">
          <CardHeader className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-t-lg">
            <CardTitle className="text-xl font-semibold">Seleccionar Fecha</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="flex gap-4 items-end">
              <div className="flex-1">
                <Label htmlFor="report-date" className="text-base font-medium">
                  Fecha del Reporte
                </Label>
                <Input
                  id="report-date"
                  type="date"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  max={new Date().toISOString().split("T")[0]}
                  className="mt-2"
                />
              </div>
              <Button onClick={loadReport} disabled={loading}>
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
                Actualizar
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Error */}
        {error && (
          <Card className="shadow-xl border-0 bg-red-50 dark:bg-red-900/20">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 text-red-600 dark:text-red-400">
                <AlertCircle className="w-6 h-6" />
                <p className="font-medium">{error}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Resumen del reporte */}
        {reportData && !loading && (
          <>
            {/* Primera fila - Métricas principales */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              {/* Ingresos Totales */}
              <Card className="shadow-xl border-0 bg-gradient-to-br from-green-500 to-green-600 text-white">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm opacity-90">Ingresos Totales</p>
                      <p className="text-2xl font-bold mt-1">
                        {formatCurrency(reportData.total_income)}
                      </p>
                    </div>
                    <TrendingUp className="w-12 h-12 opacity-80" />
                  </div>
                </CardContent>
              </Card>

              {/* Gastos Totales */}
              <Card className="shadow-xl border-0 bg-gradient-to-br from-red-500 to-red-600 text-white">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm opacity-90">Gastos Totales</p>
                      <p className="text-2xl font-bold mt-1">
                        {formatCurrency(reportData.gastos)}
                      </p>
                      <p className="text-xs opacity-80 mt-1">
                        {sessionsData.length} sesión(es)
                      </p>
                    </div>
                    <TrendingDown className="w-12 h-12 opacity-80" />
                  </div>
                </CardContent>
              </Card>

              {/* Jackpots Ganados */}
              <Card className="shadow-xl border-0 bg-gradient-to-br from-yellow-500 to-yellow-600 text-white">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm opacity-90">Jackpots Ganados</p>
                      <p className="text-2xl font-bold mt-1">
                        {formatCurrency(
                          reportData.jackpot_wins.reduce((sum, j) => sum + j.sum, 0)
                        )}
                      </p>
                      <p className="text-xs opacity-80 mt-1">
                        {reportData.jackpot_wins.length} premio(s)
                      </p>
                    </div>
                    <Calculator className="w-12 h-12 opacity-80" />
                  </div>
                </CardContent>
              </Card>

              {/* Bonos Otorgados */}
              <Card className="shadow-xl border-0 bg-gradient-to-br from-blue-500 to-blue-600 text-white">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm opacity-90">Bonos Otorgados</p>
                      <p className="text-2xl font-bold mt-1">
                        {formatCurrency(
                          reportData.bonos.reduce((sum, b) => sum + b.sum, 0)
                        )}
                      </p>
                      <p className="text-xs opacity-80 mt-1">
                        {reportData.bonos.length} bono(s)
                      </p>
                    </div>
                    <Calculator className="w-12 h-12 opacity-80" />
                  </div>
                </CardContent>
              </Card>

              {/* Egresos (Jackpots + Bonos) */}
              <Card className="shadow-xl border-0 bg-gradient-to-br from-orange-500 to-orange-600 text-white">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm opacity-90">Egresos</p>
                      <p className="text-2xl font-bold mt-1">
                        {formatCurrency(
                          reportData.jackpot_wins.reduce((sum, j) => sum + j.sum, 0) +
                          reportData.bonos.reduce((sum, b) => sum + b.sum, 0)
                        )}
                      </p>
                      <p className="text-xs opacity-80 mt-1">
                        J + B
                      </p>
                    </div>
                    <TrendingDown className="w-12 h-12 opacity-80" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Ganancias */}
            <Card
              className={`shadow-xl border-0 ${
                reportData.is_profitable
                  ? "bg-gradient-to-r from-green-500 to-green-600"
                  : "bg-gradient-to-r from-red-500 to-red-600"
              } text-white`}
            >
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-lg font-medium">Ganancias</p>
                    <p className="text-3xl font-bold mt-1">
                      {formatCurrency(reportData.ganancias)}
                    </p>
                    <p className="text-sm opacity-90 mt-1">
                      Margen: {reportData.profit_margin.toFixed(2)}%
                    </p>
                  </div>
                  {reportData.is_profitable ? (
                    <TrendingUp className="w-16 h-16 opacity-80" />
                  ) : (
                    <TrendingDown className="w-16 h-16 opacity-80" />
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Jackpots Ganados - Detalle */}
            <Card className="shadow-xl border-0 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm">
              <CardHeader 
                className="bg-gradient-to-r from-yellow-500 to-yellow-600 text-white rounded-t-lg cursor-pointer hover:from-yellow-600 hover:to-yellow-700 transition-all"
                onClick={() => setIsJackpotsExpanded(!isJackpotsExpanded)}
              >
                <div className="flex items-center justify-between">
                  <CardTitle className="text-xl font-semibold">
                    Jackpots Ganados ({jackpotsData.length}) - {formatCurrency(jackpotsData.reduce((sum, j) => sum + j.value, 0))}
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-white hover:bg-white/20"
                    onClick={(e) => {
                      e.stopPropagation()
                      setIsJackpotsExpanded(!isJackpotsExpanded)
                    }}
                  >
                    {isJackpotsExpanded ? (
                      <ChevronUp className="w-5 h-5" />
                    ) : (
                      <ChevronDown className="w-5 h-5" />
                    )}
                  </Button>
                </div>
              </CardHeader>
              {isJackpotsExpanded ? (
                <CardContent className="p-6">
                  {jackpotsData.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">
                      No hay jackpots ganados en este día
                    </p>
                  ) : (
                    <div className="space-y-3">
                      {jackpotsData.map((jackpot, index) => (
                        <div
                          key={jackpot.id}
                          className="flex items-center justify-between p-4 bg-yellow-50 dark:bg-yellow-900/10 rounded-lg border-2 border-yellow-200 dark:border-yellow-800"
                        >
                          <div className="flex items-center gap-3 flex-1">
                            <div className="bg-yellow-500 text-white rounded-full w-10 h-10 flex items-center justify-center font-bold text-sm shrink-0">
                              {index + 1}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-base font-semibold text-gray-800 dark:text-white truncate">
                                {jackpot.user_name || "Usuario desconocido"}
                              </p>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                Hora: {formatTime(jackpot.created_at)}
                              </p>
                              {jackpot.winner_hand && (
                                <p className="text-xs text-gray-500 dark:text-gray-500">
                                  Mano: {jackpot.winner_hand}
                                </p>
                              )}
                            </div>
                          </div>
                          <div className="text-right ml-4">
                            <p className="text-2xl font-bold text-yellow-700 dark:text-yellow-400">
                              {formatCurrency(jackpot.value)}
                            </p>
                          </div>
                        </div>
                      ))}
                      <div className="mt-4 pt-4 border-t-2 border-yellow-200 dark:border-yellow-800">
                        <div className="flex justify-between items-center">
                          <p className="text-lg font-semibold text-gray-700 dark:text-gray-300">
                            Total Jackpots:
                          </p>
                          <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                            {formatCurrency(jackpotsData.reduce((sum, j) => sum + j.value, 0))}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              ) : (
                <CardContent className="p-2 pb-2">
                  <div className="text-center text-gray-500 py-4">
                    <p className="text-sm">Haz clic para expandir y ver los detalles</p>
                  </div>
                </CardContent>
              )}
            </Card>

            {/* Bonos Otorgados - Detalle */}
            <Card className="shadow-xl border-0 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm">
              <CardHeader 
                className="bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-t-lg cursor-pointer hover:from-blue-600 hover:to-blue-700 transition-all"
                onClick={() => setIsBonosExpanded(!isBonosExpanded)}
              >
                <div className="flex items-center justify-between">
                  <CardTitle className="text-xl font-semibold">
                    Bonos Otorgados ({bonosData.length}) - {formatCurrency(bonosData.reduce((sum, b) => sum + b.value, 0))}
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-white hover:bg-white/20"
                    onClick={(e) => {
                      e.stopPropagation()
                      setIsBonosExpanded(!isBonosExpanded)
                    }}
                  >
                    {isBonosExpanded ? (
                      <ChevronUp className="w-5 h-5" />
                    ) : (
                      <ChevronDown className="w-5 h-5" />
                    )}
                  </Button>
                </div>
              </CardHeader>
              {isBonosExpanded ? (
                <CardContent className="p-6">
                  {bonosData.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">
                      No hay bonos otorgados en este día
                    </p>
                  ) : (
                    <div className="space-y-3">
                      {bonosData.map((bono, index) => (
                        <div
                          key={bono.id}
                          className="flex items-center justify-between p-4 bg-blue-50 dark:bg-blue-900/10 rounded-lg border-2 border-blue-200 dark:border-blue-800"
                        >
                          <div className="flex items-center gap-3 flex-1">
                            <div className="bg-blue-500 text-white rounded-full w-10 h-10 flex items-center justify-center font-bold text-sm shrink-0">
                              {index + 1}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-base font-semibold text-gray-800 dark:text-white truncate">
                                {bono.user_name || "Usuario desconocido"}
                              </p>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                Hora: {formatTime(bono.created_at)}
                              </p>
                              {bono.comment && (
                                <p className="text-xs text-gray-500 dark:text-gray-500 truncate">
                                  {bono.comment}
                                </p>
                              )}
                            </div>
                          </div>
                          <div className="text-right ml-4">
                            <p className="text-2xl font-bold text-blue-700 dark:text-blue-400">
                              {formatCurrency(bono.value)}
                            </p>
                          </div>
                        </div>
                      ))}
                      <div className="mt-4 pt-4 border-t-2 border-blue-200 dark:border-blue-800">
                        <div className="flex justify-between items-center">
                          <p className="text-lg font-semibold text-gray-700 dark:text-gray-300">
                            Total Bonos:
                          </p>
                          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                            {formatCurrency(bonosData.reduce((sum, b) => sum + b.value, 0))}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              ) : (
                <CardContent className="p-2 pb-2">
                  <div className="text-center text-gray-500 py-4">
                    <p className="text-sm">Haz clic para expandir y ver los detalles</p>
                  </div>
                </CardContent>
              )}
            </Card>

            {/* Sesiones del día */}
            <Card className="shadow-xl border-0 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm">
              <CardHeader 
                className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-t-lg cursor-pointer hover:from-indigo-600 hover:to-purple-700 transition-all"
                onClick={() => setIsSessionsExpanded(!isSessionsExpanded)}
              >
                <div className="flex items-center justify-between">
                  <CardTitle className="text-xl font-semibold">
                    Sesiones del Día ({sessionsData.length})
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-white hover:bg-white/20"
                    onClick={(e) => {
                      e.stopPropagation()
                      setIsSessionsExpanded(!isSessionsExpanded)
                    }}
                  >
                    {isSessionsExpanded ? (
                      <ChevronUp className="w-5 h-5" />
                    ) : (
                      <ChevronDown className="w-5 h-5" />
                    )}
                  </Button>
                </div>
              </CardHeader>
              {isSessionsExpanded ? (
                <CardContent className="p-6">
                  {sessionsData.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">
                      No hay sesiones registradas para este día
                    </p>
                  ) : (
                    <div className="space-y-4">
                    {sessionsData.map((session) => (
                      <Card
                        key={session.id}
                        className="border-2 border-gray-200 dark:border-gray-700"
                      >
                        <CardContent className="p-4">
                          {/* Estado y botón de editar sesión */}
                          <div className="flex justify-between items-center mb-4">
                            {/* Badge de estado */}
                            <div>
                              {session.is_active ? (
                                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 border border-green-300 dark:border-green-700">
                                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
                                  Abierto
                                </span>
                              ) : (
                                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 border border-red-300 dark:border-red-700">
                                  <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                                  Terminado
                                </span>
                              )}
                            </div>

                            {/* Botón de editar (solo para sesiones terminadas) */}
                            <div>
                              {!session.is_active && (
                                editingSessionData !== session.id ? (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => startEditingSession(session)}
                                    className="flex items-center gap-2"
                                  >
                                    <Edit2 className="w-4 h-4" />
                                    Editar Datos
                                  </Button>
                                ) : editingSessionData === session.id ? (
                                  <div className="flex gap-2">
                                    <Button
                                      size="sm"
                                      onClick={() => updateSessionData(session.id)}
                                      className="bg-green-600 hover:bg-green-700"
                                    >
                                      Guardar Cambios
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={cancelEditingSession}
                                    >
                                      Cancelar
                                    </Button>
                                  </div>
                                ) : null
                              )}
                            </div>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                Inicio
                              </p>
                              <p className="font-medium">
                                {formatDateTime(session.start_time)}
                              </p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                Fin
                              </p>
                              <p className="font-medium">
                                {session.end_time
                                  ? formatDateTime(session.end_time)
                                  : "En curso"}
                              </p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                Dealer
                              </p>
                              <p className="font-medium">
                                {session.dealer_name || "Dealer desconocido"}
                              </p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                Reik
                              </p>
                              {editingSessionData === session.id ? (
                                <Input
                                  type="number"
                                  value={editFormData.reik}
                                  onChange={(e) =>
                                    setEditFormData({ ...editFormData, reik: Number(e.target.value) })
                                  }
                                  className="mt-1"
                                  min="0"
                                />
                              ) : (
                                <p className="font-medium">{formatCurrency(session.reik)}</p>
                              )}
                            </div>
                            <div>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                Jackpot
                              </p>
                              {editingSessionData === session.id ? (
                                <Input
                                  type="number"
                                  value={editFormData.jackpot}
                                  onChange={(e) =>
                                    setEditFormData({ ...editFormData, jackpot: Number(e.target.value) })
                                  }
                                  className="mt-1"
                                  min="0"
                                />
                              ) : (
                                <p className="font-medium">
                                  {formatCurrency(session.jackpot)}
                                </p>
                              )}
                            </div>
                            <div>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                Tips (Propinas)
                              </p>
                              {editingSessionData === session.id ? (
                                <Input
                                  type="number"
                                  value={editFormData.tips}
                                  onChange={(e) =>
                                    setEditFormData({ ...editFormData, tips: Number(e.target.value) })
                                  }
                                  className="mt-1"
                                  min="0"
                                />
                              ) : (
                                <p className="font-medium">{formatCurrency(session.tips)}</p>
                              )}
                            </div>
                            <div>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                Valor por Hora
                              </p>
                              {editingSessionId === session.id ? (
                                <div className="flex gap-2 items-center mt-1">
                                  <Input
                                    type="number"
                                    value={newHourlyPay}
                                    onChange={(e) =>
                                      setNewHourlyPay(Number(e.target.value))
                                    }
                                    className="w-32"
                                    min="0"
                                  />
                                  <Button
                                    size="sm"
                                    onClick={() => updateSessionHourlyPay(session.id)}
                                  >
                                    Guardar
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => {
                                      setEditingSessionId(null)
                                      setNewHourlyPay(0)
                                    }}
                                  >
                                    Cancelar
                                  </Button>
                                </div>
                              ) : (
                                <div className="flex items-center gap-2">
                                  <p className="font-medium">
                                    {formatCurrency(session.hourly_pay)}
                                  </p>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => {
                                      setEditingSessionId(session.id)
                                      setNewHourlyPay(session.hourly_pay)
                                    }}
                                  >
                                    Editar
                                  </Button>
                                </div>
                              )}
                            </div>
                            {session.duration_hours && (
                              <div>
                                <p className="text-sm text-gray-600 dark:text-gray-400">
                                  Duración
                                </p>
                                <p className="font-medium">
                                  {session.duration_hours.toFixed(2)} horas
                                </p>
                              </div>
                            )}
                            {session.duration_hours && session.hourly_pay && (
                              <div>
                                <p className="text-sm text-gray-600 dark:text-gray-400">
                                  Valor del Turno
                                </p>
                                <p className="font-medium text-orange-600 dark:text-orange-400">
                                  {formatCurrency(Math.round(session.duration_hours * session.hourly_pay))}
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-500">
                                  {session.duration_hours.toFixed(2)}h × {formatCurrency(session.hourly_pay)}
                                </p>
                              </div>
                            )}
                          </div>
                          {session.comment && (
                            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                Comentario
                              </p>
                              <p className="text-sm mt-1">{session.comment}</p>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                    </div>
                  )}
                </CardContent>
              ) : (
                <CardContent className="p-2 pb-2">
                  <div className="text-center text-gray-500 py-4">
                    <p className="text-sm">Haz clic para expandir y ver los detalles</p>
                  </div>
                </CardContent>
              )}
            </Card>
          </>
        )}

        {/* Loading */}
        {loading && (
          <Card className="shadow-xl border-0 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm">
            <CardContent className="p-12 text-center">
              <RefreshCw className="w-12 h-12 animate-spin mx-auto text-blue-500" />
              <p className="mt-4 text-gray-600 dark:text-gray-300">
                Cargando reporte...
              </p>
            </CardContent>
          </Card>
        )}

        {/* Footer */}
        <footer className="mt-8 bg-gradient-to-r from-gray-800 to-gray-900 dark:from-gray-900 dark:to-black rounded-lg shadow-2xl" style={{ height: '300px' }}>
          <div className="h-full flex flex-col items-center justify-center text-white p-8">
            <div className="text-center space-y-4">
              <h3 className="text-2xl font-bold">Sistema de Gestión </h3>
              <div className="w-20 h-1 bg-gradient-to-r from-blue-500 to-purple-600 mx-auto rounded-full"></div>
              <p className="text-gray-300 text-lg">
                © {new Date().getFullYear()} Todos los derechos reservados
              </p>
              <p className="text-gray-400 text-sm max-w-2xl mx-auto">
                Este sistema es de uso exclusivo para la administración y gestión .
                Cualquier uso no autorizado está prohibido.
              </p>
            </div>
          </div>
        </footer>
      </div>
    </div>
  )
}

