"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DealerSession } from "@/components/dealer-session"
import { UserMenu } from "@/components/user-menu"
import {
  User,
  TrendingUp,
  TrendingDown,
  Calculator,
  RefreshCw,
  MessageSquare,
  Sun,
  Moon,
  Plus,
  Trash2,
  UserPlus,
} from "lucide-react"
import { useTheme } from "next-themes"

interface Session {
  id: number
  entrada: number
  salida: number
  comentarios: string
}

interface Player {
  id: number
  name: string
  sessions: Session[]
}

export default function PlayerPerformanceTracker() {
  const { theme, setTheme } = useTheme()

  const [players, setPlayers] = useState<Player[]>([
    {
      id: 1,
      name: "",
      sessions: [{ id: 1, entrada: 0, salida: 0, comentarios: "" }],
    },
  ])

  const updatePlayerName = (playerId: number, name: string) => {
    setPlayers((prev) => prev.map((player) => (player.id === playerId ? { ...player, name } : player)))
  }

  const updateSession = (playerId: number, sessionId: number, field: keyof Session, value: string | number) => {
    setPlayers((prev) =>
      prev.map((player) =>
        player.id === playerId
          ? {
              ...player,
              sessions: player.sessions.map((session) =>
                session.id === sessionId ? { ...session, [field]: value } : session,
              ),
            }
          : player,
      ),
    )
  }

  const addSessionToPlayer = (playerId: number) => {
    setPlayers((prev) =>
      prev.map((player) =>
        player.id === playerId
          ? {
              ...player,
              sessions: [
                ...player.sessions,
                {
                  id: Math.max(...player.sessions.map((s) => s.id)) + 1,
                  entrada: 0,
                  salida: 0,
                  comentarios: "",
                },
              ],
            }
          : player,
      ),
    )
  }

  const removeSessionFromPlayer = (playerId: number, sessionId: number) => {
    setPlayers((prev) =>
      prev.map((player) =>
        player.id === playerId && player.sessions.length > 1
          ? {
              ...player,
              sessions: player.sessions.filter((session) => session.id !== sessionId),
            }
          : player,
      ),
    )
  }

  const addNewPlayer = () => {
    const newPlayerId = Math.max(...players.map((p) => p.id)) + 1
    setPlayers((prev) => [
      ...prev,
      {
        id: newPlayerId,
        name: "",
        sessions: [{ id: 1, entrada: 0, salida: 0, comentarios: "" }],
      },
    ])
  }

  const removePlayer = (playerId: number) => {
    if (players.length > 1) {
      setPlayers((prev) => prev.filter((player) => player.id !== playerId))
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency: "COP",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const calculateBalance = (entrada: number, salida: number) => salida - entrada

  const getPlayerTotals = (player: Player) => {
    return player.sessions.reduce(
      (acc, session) => {
        const balance = calculateBalance(session.entrada, session.salida)
        return {
          entrada: acc.entrada + session.entrada,
          salida: acc.salida + session.salida,
          balance: acc.balance + balance,
          sessions: acc.sessions + 1,
        }
      },
      { entrada: 0, salida: 0, balance: 0, sessions: 0 },
    )
  }

  const grandTotals = players.reduce(
    (acc, player) => {
      const playerTotals = getPlayerTotals(player)
      return {
        entrada: acc.entrada + playerTotals.entrada,
        salida: acc.salida + playerTotals.salida,
        balance: acc.balance + playerTotals.balance,
      }
    },
    { entrada: 0, salida: 0, balance: 0 },
  )

  const resetDay = () => {
    setPlayers([
      {
        id: 1,
        name: "",
        sessions: [{ id: 1, entrada: 0, salida: 0, comentarios: "" }],
      },
    ])
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-2 sm:p-4">
      <div className="max-w-7xl mx-auto space-y-4 sm:space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between gap-2">
          <div className="text-center flex-1">
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-800 dark:text-white mb-1 sm:mb-2">📊 Ficha Diaria de Jugadores</h1>
            <p className="text-xs sm:text-sm md:text-base text-gray-600 dark:text-gray-300">Registro de Transacciones y balance diario</p>
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

        {/* Sesión del Dealer */}
        <DealerSession />

        {/* Main Table */}
        <Card className="shadow-xl border-0 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm">
          <CardHeader className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-t-lg p-4 sm:p-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <CardTitle className="text-lg sm:text-xl font-semibold">Registro de Jugadores y Transacciones</CardTitle>
              <Button
                onClick={addNewPlayer}
                variant="secondary"
                size="sm"
                className="bg-white/20 hover:bg-white/30 text-white border-white/30 w-full sm:w-auto"
              >
                <UserPlus className="w-4 h-4 mr-1" />
                Nuevo Jugador
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-blue-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-200">
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4" />
                        Jugador
                      </div>
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-200">
                      <div className="flex items-center gap-2">
                        <TrendingDown className="w-4 h-4 text-red-500" />
                        Entrada
                      </div>
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-200">
                      <div className="flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-green-500" />
                        Salida
                      </div>
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-200">
                      <div className="flex items-center gap-2">
                        <Calculator className="w-4 h-4 text-blue-500" />
                        Balance
                      </div>
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-200">
                      <div className="flex items-center gap-2">
                        <MessageSquare className="w-4 h-4 text-purple-500" />
                        Comentarios
                      </div>
                    </th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700 dark:text-gray-200">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {players.map((player) => {
                    const playerTotals = getPlayerTotals(player)

                    return player.sessions.map((session, sessionIndex) => {
                      const balance = calculateBalance(session.entrada, session.salida)
                      const isFirstSession = sessionIndex === 0
                      const isLastSession = sessionIndex === player.sessions.length - 1

                      return (
                        <tr
                          key={`${player.id}-${session.id}`}
                          className="border-b border-gray-100 dark:border-gray-600 hover:bg-blue-25 dark:hover:bg-gray-700 transition-colors"
                        >
                          <td className="px-4 py-3">
                            {isFirstSession ? (
                              <div className="flex items-center gap-2">
                                <div className="flex-1">
                                  <Input
                                    placeholder="Nombre del jugador"
                                    value={player.name}
                                    onChange={(e) => updatePlayerName(player.id, e.target.value)}
                                    className="border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                  />
                                  {player.sessions.length > 1 && (
                                    <div className="text-xs text-gray-500 mt-1">
                                      {player.sessions.length} Transacciones - Total: {formatCurrency(playerTotals.balance)}
                                    </div>
                                  )}
                                </div>
                                <div className="flex flex-col gap-1">
                                  <Button
                                    onClick={() => addSessionToPlayer(player.id)}
                                    variant="outline"
                                    size="sm"
                                    className="text-green-600 border-green-300 hover:bg-green-50 dark:hover:bg-green-900/20"
                                  >
                                    <Plus className="w-4 h-4" />
                                  </Button>
                                  {players.length > 1 && (
                                    <Button
                                      onClick={() => removePlayer(player.id)}
                                      variant="outline"
                                      size="sm"
                                      className="text-red-600 border-red-300 hover:bg-red-50 dark:hover:bg-red-900/20"
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </Button>
                                  )}
                                </div>
                              </div>
                            ) : (
                              <div className="pl-4 text-sm text-gray-500 dark:text-gray-400">
                                ↳ Transacción {sessionIndex + 1}
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <Input
                              type="number"
                              step="1000"
                              placeholder="0"
                              value={session.entrada || ""}
                              onChange={(e) =>
                                updateSession(player.id, session.id, "entrada", Number.parseFloat(e.target.value) || 0)
                              }
                              className="border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                            />
                          </td>
                          <td className="px-4 py-3">
                            <Input
                              type="number"
                              step="1000"
                              placeholder="0"
                              value={session.salida || ""}
                              onChange={(e) =>
                                updateSession(player.id, session.id, "salida", Number.parseFloat(e.target.value) || 0)
                              }
                              className="border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            />
                          </td>
                          <td className="px-4 py-3">
                            <div
                              className={`px-3 py-2 rounded-lg font-medium text-sm ${
                                balance >= 0
                                  ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                                  : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                              }`}
                            >
                              {formatCurrency(balance)}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <Input
                              placeholder="Comentarios de la Transacción"
                              value={session.comentarios}
                              onChange={(e) => updateSession(player.id, session.id, "comentarios", e.target.value)}
                              className="border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            />
                          </td>
                          <td className="px-4 py-3 text-center">
                            {!isFirstSession && (
                              <Button
                                onClick={() => removeSessionFromPlayer(player.id, session.id)}
                                variant="ghost"
                                size="sm"
                                className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            )}
                          </td>
                        </tr>
                      )
                    })
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Player Summary */}
        <Card className="shadow-lg border-0 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm">
          <CardHeader className="bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-t-lg p-4 sm:p-6">
            <CardTitle className="text-lg sm:text-xl font-semibold">Resumen por Jugador</CardTitle>
          </CardHeader>
          <CardContent className="p-4 sm:p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {players
                .filter((player) => player.name.trim())
                .map((player) => {
                  const totals = getPlayerTotals(player)
                  return (
                    <Card key={player.id} className="border border-gray-200 dark:border-gray-600">
                      <CardContent className="p-4">
                        <h3 className="font-semibold text-lg mb-2 text-gray-800 dark:text-white">{player.name}</h3>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600 dark:text-gray-400">Transacciones:</span>
                            <span className="font-medium">{totals.sessions}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-red-600 dark:text-red-400">Total Entrada:</span>
                            <span className="font-medium text-red-700 dark:text-red-300">
                              {formatCurrency(totals.entrada)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-green-600 dark:text-green-400">Total Salida:</span>
                            <span className="font-medium text-green-700 dark:text-green-300">
                              {formatCurrency(totals.salida)}
                            </span>
                          </div>
                          <div className="flex justify-between border-t pt-2">
                            <span className="text-blue-600 dark:text-blue-400 font-medium">Balance:</span>
                            <span
                              className={`font-bold ${totals.balance >= 0 ? "text-green-700 dark:text-green-300" : "text-red-700 dark:text-red-300"}`}
                            >
                              {formatCurrency(totals.balance)}
                            </span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
            </div>
          </CardContent>
        </Card>

        {/* Summary Section */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6">
          <Card className="shadow-lg border-0 bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20">
            <CardContent className="p-4 sm:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs sm:text-sm font-medium text-red-600 dark:text-red-400">Total Entrada</p>
                  <p className="text-xl sm:text-2xl font-bold text-red-800 dark:text-red-200 break-all">
                    {formatCurrency(grandTotals.entrada)}
                  </p>
                </div>
                <TrendingDown className="w-6 h-6 sm:w-8 sm:h-8 text-red-500 shrink-0" />
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-lg border-0 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20">
            <CardContent className="p-4 sm:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs sm:text-sm font-medium text-green-600 dark:text-green-400">Total Salida</p>
                  <p className="text-xl sm:text-2xl font-bold text-green-800 dark:text-green-200 break-all">
                    {formatCurrency(grandTotals.salida)}
                  </p>
                </div>
                <TrendingUp className="w-6 h-6 sm:w-8 sm:h-8 text-green-500 shrink-0" />
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-lg border-0 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 sm:col-span-2 md:col-span-1">
            <CardContent className="p-4 sm:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs sm:text-sm font-medium text-blue-600 dark:text-blue-400">Balance Total</p>
                  <p className="text-xl sm:text-2xl font-bold text-blue-800 dark:text-blue-200 break-all">
                    {formatCurrency(grandTotals.balance)}
                  </p>
                </div>
                <Calculator className="w-6 h-6 sm:w-8 sm:h-8 text-blue-500 shrink-0" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Reset Button */}
        <div className="flex justify-center px-2">
          <Button
            onClick={resetDay}
            size="lg"
            className="w-full sm:w-auto bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-semibold py-4 px-8 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
          >
            <RefreshCw className="w-5 h-5 mr-2" />🆕 Nuevo Día
          </Button>
        </div>
      </div>
    </div>
  )
}
