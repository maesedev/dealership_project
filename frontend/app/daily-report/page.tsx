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
  net_profit: number
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
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null)
  const [newHourlyPay, setNewHourlyPay] = useState<number>(0)

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
        const sessionsPromises = report.sessions.map((sessionId) =>
          api.get<SessionData>(`/api/v1/sessions/${sessionId}`)
        )
        const sessions = await Promise.all(sessionsPromises)
        setSessionsData(sessions)
      } else {
        setSessionsData([])
      }
    } catch (err: any) {
      console.error("Error al cargar reporte:", err)
      setError(err.message || "Error al cargar el reporte")
      setReportData(null)
      setSessionsData([])
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
    } catch (err: any) {
      console.error("Error al actualizar sesión:", err)
      alert("Error al actualizar el valor por hora: " + err.message)
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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

              {/* Egresos Totales */}
              <Card className="shadow-xl border-0 bg-gradient-to-br from-red-500 to-red-600 text-white">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm opacity-90">Egresos Totales</p>
                      <p className="text-2xl font-bold mt-1">
                        {formatCurrency(reportData.gastos)}
                      </p>
                    </div>
                    <TrendingDown className="w-12 h-12 opacity-80" />
                  </div>
                </CardContent>
              </Card>

              {/* Jackpots Totales */}
              <Card className="shadow-xl border-0 bg-gradient-to-br from-yellow-500 to-yellow-600 text-white">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm opacity-90">Jackpots</p>
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

              {/* Bonos Totales */}
              <Card className="shadow-xl border-0 bg-gradient-to-br from-blue-500 to-blue-600 text-white">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm opacity-90">Bonos</p>
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
            </div>

            {/* Ganancia Neta */}
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
                    <p className="text-lg font-medium">Ganancia Neta</p>
                    <p className="text-3xl font-bold mt-1">
                      {formatCurrency(reportData.net_profit)}
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

            {/* Sesiones del día */}
            <Card className="shadow-xl border-0 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm">
              <CardHeader className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-t-lg">
                <CardTitle className="text-xl font-semibold">
                  Sesiones del Día ({sessionsData.length})
                </CardTitle>
              </CardHeader>
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
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                                Reik
                              </p>
                              <p className="font-medium">{formatCurrency(session.reik)}</p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                Jackpot
                              </p>
                              <p className="font-medium">
                                {formatCurrency(session.jackpot)}
                              </p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                Tips
                              </p>
                              <p className="font-medium">{formatCurrency(session.tips)}</p>
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
      </div>
    </div>
  )
}

