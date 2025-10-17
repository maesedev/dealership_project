"use client"

import React, { useState, useEffect, useRef } from "react"
import { useAuth } from "@/lib/auth-context"
import { api } from "@/lib/api-client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { DealerSession } from "@/components/dealer-session"
import { UserMenu } from "@/components/user-menu"
import { AdminNavigation } from "@/components/admin-navigation"
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
  AlertCircle,
  Search,
} from "lucide-react"
import { useTheme } from "next-themes"
import { Switch } from "@/components/ui/switch"

interface Transaction {
  id: string
  user_id: string
  session_id: string
  cantidad: number
  operation_type: "CASH IN" | "CASH OUT"
  transaction_media: "DIGITAL" | "CASH"
  comment: string
  created_at: string
  updated_at: string
  signed_amount: number
}

interface Bono {
  id: string
  user_id: string
  session_id: string
  value: number
  comment: string
  created_at: string
  updated_at: string
  type: "BONO" // Para distinguir en la UI
}

interface JackpotPrice {
  id: string
  user_id: string
  session_id: string
  value: number
  winner_hand: string
  comment: string
  created_at: string
  updated_at: string
  type: "JACKPOT" // Para distinguir en la UI
}

interface UserSearchResult {
  id: string
  username: string
  name: string
  roles: string[]
  is_active: boolean
}

interface Player {
  id: number
  name: string
  userId: string | null
  searchQuery: string
  searchResults: UserSearchResult[]
  showSearchResults: boolean
  transactions: Transaction[]
  bonos: Bono[]
  jackpots: JackpotPrice[]
  borderColor: string
}

export default function PlayerPerformanceTracker() {
  const { theme, setTheme } = useTheme()
  const { user } = useAuth()
  const [hasActiveSession, setHasActiveSession] = useState(false)
  const [isCheckingSession, setIsCheckingSession] = useState(true)
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const searchTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined)
  
  // Estados para modales de bono y jackpot
  const [showBonoModal, setShowBonoModal] = useState(false)
  const [showJackpotModal, setShowJackpotModal] = useState(false)
  const [selectedPlayerForBono, setSelectedPlayerForBono] = useState<string | null>(null)
  const [bonoAmount, setBonoAmount] = useState<number>(0)
  const [bonoComment, setBonoComment] = useState<string>("")
  const [jackpotAmount, setJackpotAmount] = useState<number>(0)
  const [jackpotComment, setJackpotComment] = useState<string>("")
  const [winnerHand, setWinnerHand] = useState<string>("")

  // Función para generar un color aleatorio para el borde
  const generateRandomBorderColor = () => {
    const colors = [
      'border-red-400',
      'border-blue-400',
      'border-green-400',
      'border-yellow-400',
      'border-purple-400',
      'border-pink-400',
      'border-indigo-400',
      'border-orange-400',
      'border-teal-400',
      'border-cyan-400',
    ]
    return colors[Math.floor(Math.random() * colors.length)]
  }

  const [players, setPlayers] = useState<Player[]>(() => [
    {
      id: 1,
      name: "",
      userId: null,
      searchQuery: "",
      searchResults: [],
      showSearchResults: false,
      transactions: [],
      bonos: [],
      jackpots: [],
      borderColor: generateRandomBorderColor(),
    },
  ])

  // Verificar si hay una sesión activa y cargar transacciones
  useEffect(() => {
    // Cargar transacciones, bonos y jackpots de una sesión
    const loadTransactionsForSession = async (sessionId: string) => {
      try {
        // Cargar transacciones
        let transactions: Transaction[] = []
        try {
          const transactionsResponse = await api.get(`/api/v1/transactions/session/${sessionId}`)
          transactions = transactionsResponse.transactions || []
        } catch (error) {
          console.error('Error al cargar transacciones:', error)
        }
        
        // Cargar bonos (puede fallar si el endpoint no existe)
        let bonos: any[] = []
        try {
          const bonosResponse = await api.get(`/api/v1/bonos/session/${sessionId}`)
          bonos = bonosResponse.bonos || []
        } catch (error) {
          console.warn('No se pudieron cargar bonos (endpoint podría no existir):', error)
        }
        
        // Cargar jackpots (puede fallar si el endpoint no existe)
        let jackpots: any[] = []
        try {
          const jackpotsResponse = await api.get(`/api/v1/jackpot-prices/session/${sessionId}`)
          jackpots = jackpotsResponse.jackpot_prices || []
        } catch (error) {
          console.warn('No se pudieron cargar jackpots (endpoint podría no existir):', error)
        }
        
        // Agrupar por usuario
        const dataByUser = new Map<string, { transactions: Transaction[], bonos: Bono[], jackpots: JackpotPrice[] }>()
        
        // Agregar transacciones
        for (const transaction of transactions) {
          if (!dataByUser.has(transaction.user_id)) {
            dataByUser.set(transaction.user_id, { transactions: [], bonos: [], jackpots: [] })
          }
          dataByUser.get(transaction.user_id)!.transactions.push(transaction)
        }
        
        // Agregar bonos
        for (const bono of bonos) {
          if (!dataByUser.has(bono.user_id)) {
            dataByUser.set(bono.user_id, { transactions: [], bonos: [], jackpots: [] })
          }
          dataByUser.get(bono.user_id)!.bonos.push({ ...bono, type: "BONO" as const })
        }
        
        // Agregar jackpots
        for (const jackpot of jackpots) {
          if (!dataByUser.has(jackpot.user_id)) {
            dataByUser.set(jackpot.user_id, { transactions: [], bonos: [], jackpots: [] })
          }
          dataByUser.get(jackpot.user_id)!.jackpots.push({ ...jackpot, type: "JACKPOT" as const })
        }
        
        // Crear jugadores con sus datos
        const loadedPlayers: Player[] = []
        let playerId = 1
        
        for (const [userId, data] of dataByUser.entries()) {
          // Obtener información del usuario
          try {
            const userResponse = await api.get(`/api/v1/users/${userId}`)
            loadedPlayers.push({
              id: playerId++,
              name: userResponse.name || "",
              userId: userId,
              searchQuery: userResponse.name || "",
              searchResults: [],
              showSearchResults: false,
              transactions: data.transactions,
              bonos: data.bonos,
              jackpots: data.jackpots,
              borderColor: generateRandomBorderColor(),
            })
          } catch (error) {
            console.error('Error al cargar usuario:', error)
          }
        }
        
        if (loadedPlayers.length > 0) {
          setPlayers(loadedPlayers)
        }
      } catch (error) {
        console.error('Error al cargar datos de la sesión:', error)
      }
    }

    const checkActiveSession = async () => {
      if (!user?.id) {
        setIsCheckingSession(false)
        return
      }

      try {
        const response = await api.get(`/api/v1/sessions/active/user/${user.id}`)
        const hasActive = response.sessions && response.sessions.length > 0
        setHasActiveSession(hasActive)
        
        if (hasActive && response.sessions[0]) {
          const sessionId = response.sessions[0].id
          setActiveSessionId(sessionId)
          
          // Cargar transacciones existentes
          await loadTransactionsForSession(sessionId)
        }
      } catch (error) {
        console.error('Error al verificar sesión activa:', error)
        setHasActiveSession(false)
      } finally {
        setIsCheckingSession(false)
      }
    }

    checkActiveSession()
  }, [user?.id])

  // Buscar usuarios por nombre
  const searchUsers = async (playerId: number, query: string) => {
    if (query.length < 2) {
      setPlayers((prev) =>
        prev.map((player) =>
          player.id === playerId
            ? { ...player, searchResults: [], showSearchResults: false }
            : player
        )
      )
      return
    }

    try {
      console.log('Buscando usuarios con query:', query)
      const response = await api.get(`/api/v1/users/search/by-username?q=${encodeURIComponent(query)}`)
      console.log('Respuesta de búsqueda:', response)
      
      const users = response.users || []
      console.log('Usuarios encontrados:', users.length)
      
      // Siempre mostrar el dropdown si hay al menos 2 caracteres (para mostrar la opción de crear)
      setPlayers((prev) =>
        prev.map((player) =>
          player.id === playerId
            ? { ...player, searchResults: users, showSearchResults: true }
            : player
        )
      )
    } catch (error) {
      console.error('Error al buscar usuarios:', error)
      // Aún así mostrar el dropdown para permitir crear usuario
      setPlayers((prev) =>
        prev.map((player) =>
          player.id === playerId
            ? { ...player, searchResults: [], showSearchResults: true }
            : player
        )
      )
    }
  }

  // Actualizar query de búsqueda
  const updateSearchQuery = (playerId: number, query: string) => {
    setPlayers((prev) =>
      prev.map((player) =>
        player.id === playerId 
          ? { 
              ...player, 
              searchQuery: query, 
              name: "", 
              userId: null,  // Limpiar el usuario seleccionado
              searchResults: [],  // Limpiar resultados de búsqueda
              showSearchResults: false  // Ocultar dropdown
            } 
          : player
      )
    )

    // Cancelar búsqueda anterior
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }

    // Realizar búsqueda con debounce
    searchTimeoutRef.current = setTimeout(() => {
      searchUsers(playerId, query)
    }, 300)
  }

  // Seleccionar un usuario de los resultados
  const selectUser = (playerId: number, user: UserSearchResult) => {
    setPlayers((prev) =>
      prev.map((player) =>
        player.id === playerId
          ? {
              ...player,
              name: user.name,
              userId: user.id,
              searchQuery: user.name,
              showSearchResults: false,
              searchResults: [],
            }
          : player
      )
    )
  }

  // Crear nuevo usuario
  const createNewUser = async (playerId: number, userName: string) => {
    try {
      console.log('Creando nuevo usuario con nombre:', userName)
      
      const newUserData = {
        name: userName,
        roles: ["USER"]
      }
      
      const response = await api.post('/api/v1/users/create', newUserData)
      console.log('Usuario creado:', response)
      
      // Seleccionar el usuario recién creado
    setPlayers((prev) =>
      prev.map((player) =>
        player.id === playerId
          ? {
              ...player,
                name: response.name,
                userId: response.id,
                searchQuery: response.name,
                showSearchResults: false,
                searchResults: [],
              }
            : player
        )
      )
      
      alert(`Usuario "${userName}" creado exitosamente`)
    } catch (error) {
      console.error('Error al crear usuario:', error)
      alert('Error al crear usuario')
    }
  }

  // Agregar transacción a un jugador
  const addTransactionToPlayer = async (playerId: number) => {
    const player = players.find((p) => p.id === playerId)
    if (!player || !player.userId || !activeSessionId) return

    try {
      const newTransaction = {
        user_id: player.userId,
        session_id: activeSessionId,
                  cantidad: 0,
        operation_type: "CASH IN",
        transaction_media: "DIGITAL",
        comment: "",
      }

      const response = await api.post('/api/v1/transactions', newTransaction)
      
      setPlayers((prev) =>
        prev.map((p) =>
          p.id === playerId
            ? { ...p, transactions: [...p.transactions, response] }
            : p
        )
      )
    } catch (error) {
      console.error('Error al crear transacción:', error)
      alert('Error al crear transacción')
    }
  }

  // Actualizar transacción
  const updateTransaction = async (
    playerId: number,
    transactionId: string,
    field: keyof Transaction,
    value: any
  ) => {
    const player = players.find((p) => p.id === playerId)
    if (!player) return

    // Actualizar localmente primero para mejor UX
    setPlayers((prev) =>
      prev.map((p) =>
        p.id === playerId
          ? {
              ...p,
              transactions: p.transactions.map((t) =>
                t.id === transactionId ? { ...t, [field]: value } : t
              ),
            }
          : p
      )
    )

    // Luego actualizar en el backend
    try {
      const transaction = player.transactions.find((t) => t.id === transactionId)
      if (!transaction) return

      const updateData: any = {}
      
      if (field === 'cantidad') {
        updateData.cantidad = value
      } else if (field === 'operation_type') {
        updateData.operation_type = value
      } else if (field === 'transaction_media') {
        updateData.transaction_media = value
      } else if (field === 'comment') {
        updateData.comment = value
      }

      await api.put(`/api/v1/transactions/${transactionId}`, updateData)
    } catch (error) {
      console.error('Error al actualizar transacción:', error)
      alert('Error al actualizar transacción')
    }
  }

  // Eliminar transacción
  const removeTransactionFromPlayer = async (playerId: number, transactionId: string) => {
    try {
      const response = await api.delete(`/api/v1/transactions/${transactionId}`)
      console.log('Transacción eliminada exitosamente:', response)
      
    setPlayers((prev) =>
      prev.map((player) =>
        player.id === playerId
          ? {
              ...player,
                transactions: player.transactions.filter((t) => t.id !== transactionId),
            }
            : player
        )
    )
    } catch (error) {
      console.error('Error al eliminar transacción:', error)
      alert('Error al eliminar transacción')
    }
  }

  // Agregar bono
  const addBono = async () => {
    if (!selectedPlayerForBono || !activeSessionId) return
    
    try {
      const newBono = {
        user_id: selectedPlayerForBono,
        session_id: activeSessionId,
        value: bonoAmount,
        comment: bonoComment,
      }
      
      const response = await api.post('/api/v1/bonos', newBono)
      
      setPlayers((prev) =>
        prev.map((p) =>
          p.userId === selectedPlayerForBono
            ? { ...p, bonos: [...p.bonos, { ...response, type: "BONO" as const }] }
            : p
        )
      )
      
      // Cerrar modal y limpiar campos
      setShowBonoModal(false)
      setSelectedPlayerForBono(null)
      setBonoAmount(0)
      setBonoComment("")
    } catch (error) {
      console.error('Error al crear bono:', error)
      alert('Error al crear bono')
    }
  }

  // Actualizar bono
  const updateBono = async (playerId: number, bonoId: string, field: keyof Bono, value: any) => {
    const player = players.find((p) => p.id === playerId)
    if (!player) return

    // Actualizar localmente primero
    setPlayers((prev) =>
      prev.map((p) =>
        p.id === playerId
          ? {
              ...p,
              bonos: p.bonos.map((b) =>
                b.id === bonoId ? { ...b, [field]: value } : b
              ),
            }
          : p
      )
    )

    // Actualizar en el backend
    try {
      const updateData: any = {}
      if (field === 'value') {
        updateData.value = value
      } else if (field === 'comment') {
        updateData.comment = value
      }

      await api.put(`/api/v1/bonos/${bonoId}`, updateData)
    } catch (error) {
      console.error('Error al actualizar bono:', error)
      alert('Error al actualizar bono')
    }
  }

  // Eliminar bono
  const removeBono = async (playerId: number, bonoId: string) => {
    try {
      await api.delete(`/api/v1/bonos/${bonoId}`)
      
      setPlayers((prev) =>
        prev.map((player) =>
          player.id === playerId
            ? {
                ...player,
                bonos: player.bonos.filter((b) => b.id !== bonoId),
              }
            : player
        )
      )
    } catch (error) {
      console.error('Error al eliminar bono:', error)
      alert('Error al eliminar bono')
    }
  }

  // Agregar jackpot
  const addJackpot = async () => {
    if (!selectedPlayerForBono || !activeSessionId) return
    
    try {
      const newJackpot = {
        user_id: selectedPlayerForBono,
        session_id: activeSessionId,
        value: jackpotAmount,
        winner_hand: winnerHand,
        comment: jackpotComment,
      }
      
      const response = await api.post('/api/v1/jackpot-prices', newJackpot)
      
      setPlayers((prev) =>
        prev.map((p) =>
          p.userId === selectedPlayerForBono
            ? { ...p, jackpots: [...p.jackpots, { ...response, type: "JACKPOT" as const }] }
            : p
        )
      )
      
      // Cerrar modal y limpiar campos
      setShowJackpotModal(false)
      setSelectedPlayerForBono(null)
      setJackpotAmount(0)
      setJackpotComment("")
      setWinnerHand("")
    } catch (error) {
      console.error('Error al crear jackpot:', error)
      alert('Error al crear jackpot')
    }
  }

  // Actualizar jackpot
  const updateJackpot = async (playerId: number, jackpotId: string, field: keyof JackpotPrice, value: any) => {
    const player = players.find((p) => p.id === playerId)
    if (!player) return

    // Actualizar localmente primero
    setPlayers((prev) =>
      prev.map((p) =>
        p.id === playerId
          ? {
              ...p,
              jackpots: p.jackpots.map((j) =>
                j.id === jackpotId ? { ...j, [field]: value } : j
              ),
            }
          : p
      )
    )

    // Actualizar en el backend
    try {
      const updateData: any = {}
      if (field === 'value') {
        updateData.value = value
      } else if (field === 'comment') {
        updateData.comment = value
      } else if (field === 'winner_hand') {
        updateData.winner_hand = value
      }

      await api.put(`/api/v1/jackpot-prices/${jackpotId}`, updateData)
    } catch (error) {
      console.error('Error al actualizar jackpot:', error)
      alert('Error al actualizar jackpot')
    }
  }

  // Eliminar jackpot
  const removeJackpot = async (playerId: number, jackpotId: string) => {
    try {
      await api.delete(`/api/v1/jackpot-prices/${jackpotId}`)
      
      setPlayers((prev) =>
        prev.map((player) =>
          player.id === playerId
            ? {
                ...player,
                jackpots: player.jackpots.filter((j) => j.id !== jackpotId),
              }
            : player
        )
      )
    } catch (error) {
      console.error('Error al eliminar jackpot:', error)
      alert('Error al eliminar jackpot')
    }
  }

  const addNewPlayer = () => {
    const newPlayerId = Math.max(...players.map((p) => p.id)) + 1
    setPlayers((prev) => [
      ...prev,
      {
        id: newPlayerId,
        name: "",
        userId: null,
        searchQuery: "",
        searchResults: [],
        showSearchResults: false,
        transactions: [],
        bonos: [],
        jackpots: [],
        borderColor: generateRandomBorderColor(),
      },
    ])
  }

  const removePlayer = async (playerId: number) => {
    if (players.length > 1) {
      const player = players.find((p) => p.id === playerId)
      
      // Eliminar todas las transacciones del jugador
      if (player && player.transactions.length > 0) {
        try {
          for (const transaction of player.transactions) {
            await api.delete(`/api/v1/transactions/${transaction.id}`)
          }
        } catch (error) {
          console.error('Error al eliminar transacciones del jugador:', error)
        }
      }
      
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

  const calculateBalance = (cantidad: number, tipo: "CASH IN" | "CASH OUT") => {
    return tipo === "CASH IN" ? cantidad : -cantidad
  }

  const getPlayerTotals = (player: Player) => {
    const transactionTotals = player.transactions.reduce(
      (acc, transaction) => {
        const balance = calculateBalance(transaction.cantidad, transaction.operation_type)
        const cashIn = transaction.operation_type === "CASH IN" ? transaction.cantidad : 0
        const cashOut = transaction.operation_type === "CASH OUT" ? transaction.cantidad : 0
        return {
          cashIn: acc.cashIn + cashIn,
          cashOut: acc.cashOut + cashOut,
          balance: acc.balance + balance,
          transactions: acc.transactions + 1,
        }
      },
      { cashIn: 0, cashOut: 0, balance: 0, transactions: 0 },
    )
    
    // Agregar bonos al balance (suma positiva)
    const bonosTotal = player.bonos.reduce((sum, bono) => sum + bono.value, 0)
    
    // Agregar jackpots al balance (suma positiva)
    const jackpotsTotal = player.jackpots.reduce((sum, jackpot) => sum + jackpot.value, 0)
    
    return {
      cashIn: transactionTotals.cashIn,
      cashOut: transactionTotals.cashOut,
      balance: transactionTotals.balance + bonosTotal + jackpotsTotal,
      transactions: transactionTotals.transactions,
      bonos: player.bonos.length,
      jackpots: player.jackpots.length,
      bonosTotal,
      jackpotsTotal,
    }
  }

  const grandTotals = players.reduce(
    (acc, player) => {
      const playerTotals = getPlayerTotals(player)
      return {
        cashIn: acc.cashIn + playerTotals.cashIn,
        cashOut: acc.cashOut + playerTotals.cashOut,
        balance: acc.balance + playerTotals.balance,
      }
    },
    { cashIn: 0, cashOut: 0, balance: 0 },
  )

  // Limpiar datos de la sesión cuando se termina el turno
  const clearSessionData = () => {
    console.log('Limpiando datos de la sesión anterior...')
    setPlayers([
      {
        id: 1,
        name: "",
        userId: null,
        searchQuery: "",
        searchResults: [],
        showSearchResults: false,
        transactions: [],
        bonos: [],
        jackpots: [],
        borderColor: generateRandomBorderColor(),
      },
    ])
    setActiveSessionId(null)
  }

  // Actualizar el ID de sesión activa cuando se inicia una nueva sesión
  const updateActiveSessionId = async () => {
    if (!user?.id) return

    try {
      const response = await api.get(`/api/v1/sessions/active/user/${user.id}`)
      const hasActive = response.sessions && response.sessions.length > 0
      
      if (hasActive && response.sessions[0]) {
        const sessionId = response.sessions[0].id
        setActiveSessionId(sessionId)
        console.log('Nueva sesión activa:', sessionId)
      }
    } catch (error) {
      console.error('Error al actualizar sesión activa:', error)
    }
  }

  const resetDay = async () => {
    // Eliminar todas las transacciones, bonos y jackpots
    for (const player of players) {
      // Eliminar transacciones
      for (const transaction of player.transactions) {
        try {
          await api.delete(`/api/v1/transactions/${transaction.id}`)
        } catch (error) {
          console.error('Error al eliminar transacción:', error)
        }
      }
      
      // Eliminar bonos (si existen)
      if (player.bonos && player.bonos.length > 0) {
        for (const bono of player.bonos) {
          try {
            await api.delete(`/api/v1/bonos/${bono.id}`)
          } catch (error) {
            console.warn('Error al eliminar bono (endpoint podría no existir):', error)
          }
        }
      }
      
      // Eliminar jackpots (si existen)
      if (player.jackpots && player.jackpots.length > 0) {
        for (const jackpot of player.jackpots) {
          try {
            await api.delete(`/api/v1/jackpot-prices/${jackpot.id}`)
          } catch (error) {
            console.warn('Error al eliminar jackpot (endpoint podría no existir):', error)
          }
        }
      }
    }
    
    setPlayers([
      {
        id: 1,
        name: "",
        userId: null,
        searchQuery: "",
        searchResults: [],
        showSearchResults: false,
        transactions: [],
        bonos: [],
        jackpots: [],
        borderColor: generateRandomBorderColor(),
      },
    ])
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-2 sm:p-4">
      <div className="max-w-full sm:max-w-[90vw] md:max-w-[85vw] lg:max-w-[80vw] xl:max-w-[75vw] mx-auto space-y-4 sm:space-y-6">
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

        {/* Admin Link */}
        <AdminNavigation />

        {/* Sesión del Dealer */}
        <DealerSession 
          onSessionChange={setHasActiveSession} 
          onSessionEnd={clearSessionData}
          onSessionStart={updateActiveSessionId}
        />

        {/* Mensaje cuando no hay sesión activa */}
        {!isCheckingSession && !hasActiveSession && (
          <Card className="shadow-xl border-0 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm">
            <CardContent className="p-8 text-center">
              <div className="flex flex-col items-center gap-4">
                <AlertCircle className="h-16 w-16 text-orange-500" />
                <div>
                  <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">
                    No hay turno activo
                  </h2>
                  <p className="text-gray-600 dark:text-gray-300 mb-4">
                    Para registrar jugadores y transacciones, primero debes iniciar un turno.
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Haz clic en "Iniciar Turno" en la sección de arriba para comenzar.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Main Table - Solo mostrar si hay sesión activa */}
        {hasActiveSession && (() => {
          // Calcular si hay algún dropdown visible
          const hasVisibleDropdown = players.some(player => 
            !player.transactions.length && player.showSearchResults && player.searchQuery.length >= 2
          )
          
          return (
            <Card className="shadow-xl border-0 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm" style={{ overflow: 'visible' }}>
            <CardHeader className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-t-lg p-4 sm:p-6">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <CardTitle className="text-lg sm:text-xl font-semibold">Registro de Jugadores y Transacciones</CardTitle>
                <div className="flex flex-wrap gap-2 w-full sm:w-auto">
                  <Button
                    onClick={addNewPlayer}
                    variant="secondary"
                    size="sm"
                    className="bg-white/20 hover:bg-white/30 text-white border-white/30 flex-1 sm:flex-none"
                  >
                    <UserPlus className="w-4 h-4 mr-1" />
                    Nuevo Jugador
                  </Button>
                  <Button
                    onClick={() => setShowBonoModal(true)}
                    variant="secondary"
                    size="sm"
                    className="bg-green-500/80 hover:bg-green-600/80 text-white border-white/30 flex-1 sm:flex-none"
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    Agregar Bono
                  </Button>
                  <Button
                    onClick={() => setShowJackpotModal(true)}
                    variant="secondary"
                    size="sm"
                    className="bg-yellow-500/80 hover:bg-yellow-600/80 text-white border-white/30 flex-1 sm:flex-none"
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    Agregar Jackpot
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0" style={{ overflow: 'visible' }}>
              <div className="overflow-x-auto" style={{ 
                overflowY: 'visible', 
                position: 'relative', 
                minHeight: hasVisibleDropdown ? '400px' : '200px',
                transition: 'min-height 0.3s ease-in-out'
              }}>
                <table className="w-full min-w-[1000px]">
                <thead className="bg-blue-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-200 w-[30%] min-w-[200px]">
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4" />
                        Jugador
                      </div>
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-200 w-[15%] min-w-[100px]">
                      <div className="flex items-center gap-2">
                        <Calculator className="w-4 h-4 text-blue-500" />
                        Cantidad
                      </div>
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-200 w-[12%] min-w-[80px]">
                      <div className="flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-green-500" />
                        Tipo
                      </div>
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-200 w-[15%] min-w-[110px]">
                      <div className="flex items-center gap-2">
                        <Calculator className="w-4 h-4 text-orange-500" />
                        Medio de Pago
                      </div>
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-200 w-[12%] min-w-[80px]">
                      <div className="flex items-center gap-2">
                        <Calculator className="w-4 h-4 text-blue-500" />
                        Balance
                      </div>
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-200 w-[16%] min-w-[120px]">
                      <div className="flex items-center gap-2">
                        <MessageSquare className="w-4 h-4 text-purple-500" />
                        Comentarios
                      </div>
                    </th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700 dark:text-gray-200 w-[5%] min-w-[60px]">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {players.map((player) => {
                    const playerTotals = getPlayerTotals(player)
                    const hasUserId = player.userId !== null
                    
                    // Debug: ver el estado del dropdown
                    if (player.searchQuery.length >= 2) {
                      console.log(`Player ${player.id} - Query: "${player.searchQuery}", ShowResults: ${player.showSearchResults}, Results count: ${player.searchResults.length}`)
                    }

                    return (
                      <React.Fragment key={player.id}>
                        {/* Fila del jugador */}
                        <tr className="border-b border-gray-100 dark:border-gray-600 hover:bg-blue-25 dark:hover:bg-gray-700 transition-colors">
                          <td className="px-4 py-3 w-[30%] min-w-[200px]">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 relative">
                                <div className={`border-2 ${player.userId ? player.borderColor : 'border-gray-300 dark:border-gray-600'} rounded-lg p-2 ${player.transactions.length > 0 ? 'bg-gray-100 dark:bg-gray-700/50' : ''}`}>
                                  <div className="flex items-center gap-2">
                                    <Search className="w-4 h-4 text-gray-400" />
                                <Input
                                      placeholder="Buscar jugador..."
                                      value={player.searchQuery}
                                      onChange={(e) => updateSearchQuery(player.id, e.target.value)}
                                      disabled={player.transactions.length > 0}
                                      className={`border-0 focus:ring-0 focus:outline-none focus:border-0 focus:shadow-none focus:bg-transparent p-0 h-auto ${player.transactions.length > 0 ? 'bg-transparent cursor-not-allowed opacity-70' : ''}`}
                                      title={player.transactions.length > 0 ? 'No se puede cambiar el jugador después de crear transacciones' : ''}
                                      style={{ boxShadow: 'none', outline: 'none' }}
                                    />
                                  </div>
                                </div>
                                
                                {/* Dropdown de resultados de búsqueda - solo si no hay transacciones */}
                                {!player.transactions.length && player.showSearchResults && player.searchQuery.length >= 2 && (() => {
                                  // Verificar si existe un usuario con el mismo nombre exacto (case insensitive)
                                  const exactMatch = player.searchResults.some(
                                    (userResult) => userResult.name.toLowerCase() === player.searchQuery.toLowerCase()
                                  )
                                  const showCreateOption = !exactMatch
                                  
                                  console.log('Renderizando dropdown para player', player.id, 'con', player.searchResults.length, 'resultados')
                                  
                                  return (
                                    <div 
                                      className="absolute bg-white dark:bg-gray-800 border-2 border-blue-400 dark:border-blue-600 rounded-lg shadow-2xl max-h-64 overflow-y-auto"
                                      style={{ 
                                        position: 'absolute',
                                        top: '100%',
                                        left: 0,
                                        right: 0,
                                        width: '100%',
                                        marginTop: '4px'
                                      }}
                                    >
                                      {player.searchResults.length > 0 ? (
                                        <>
                                          {player.searchResults.map((userResult) => (
                                            <button
                                              key={userResult.id}
                                              onClick={() => {
                                                console.log('Usuario seleccionado:', userResult)
                                                selectUser(player.id, userResult)
                                              }}
                                              className="w-full text-left px-4 py-2 hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors border-b border-gray-100 dark:border-gray-600"
                                            >
                                              <div className="font-medium text-gray-800 dark:text-white">
                                                {userResult.name}
                                              </div>
                                              {userResult.username && (
                                                <div className="text-xs text-gray-500 dark:text-gray-400">
                                                  @{userResult.username}
                                                </div>
                                              )}
                                            </button>
                                          ))}
                                          {/* Opción para crear nuevo usuario - solo si no hay match exacto */}
                                          {showCreateOption && (
                                            <button
                                              onClick={() => createNewUser(player.id, player.searchQuery)}
                                              className="w-full text-left px-4 py-3 hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors border-t-2 border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50"
                                            >
                                              <div className="flex items-center gap-2">
                                                <UserPlus className="w-4 h-4 text-green-600 dark:text-green-400" />
                                                <div>
                                                  <div className="font-medium text-green-600 dark:text-green-400">
                                                    Crear nuevo usuario
                                                  </div>
                                                  <div className="text-xs text-gray-500 dark:text-gray-400">
                                                    Crear "{player.searchQuery}" como nuevo jugador
                                                  </div>
                                                </div>
                                              </div>
                                            </button>
                                          )}
                                        </>
                                      ) : (
                                        /* Si no hay resultados, mostrar opción de crear */
                                        <button
                                          onClick={() => createNewUser(player.id, player.searchQuery)}
                                          className="w-full text-left px-4 py-3 hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
                                        >
                                          <div className="flex items-center gap-2">
                                            <UserPlus className="w-4 h-4 text-green-600 dark:text-green-400" />
                                            <div>
                                              <div className="font-medium text-green-600 dark:text-green-400">
                                                Crear nuevo usuario
                                              </div>
                                              <div className="text-xs text-gray-500 dark:text-gray-400">
                                                No se encontraron resultados. Crear "{player.searchQuery}" como nuevo jugador
                                              </div>
                                            </div>
                                          </div>
                                        </button>
                                      )}
                                    </div>
                                  )
                                })()}
                                
                                {(player.transactions.length > 0 || player.bonos.length > 0 || player.jackpots.length > 0) && (
                                  <div className="text-xs text-gray-500 mt-1">
                                    {player.transactions.length} Trans. 
                                    {player.bonos.length > 0 && ` | ${player.bonos.length} Bono(s)`}
                                    {player.jackpots.length > 0 && ` | ${player.jackpots.length} Jackpot(s)`}
                                    {' - Total: '}{formatCurrency(playerTotals.balance)}
                                  </div>
                                )}
                              </div>
                              <div className="flex flex-col gap-1">
                                  <Button
                                  onClick={() => addTransactionToPlayer(player.id)}
                                    variant="outline"
                                    size="sm"
                                  disabled={!hasUserId}
                                  className={`${hasUserId ? "text-green-600 border-green-300 hover:bg-green-50 dark:hover:bg-green-900/20" : "opacity-50 cursor-not-allowed"}`}
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
                          </td>
                          <td className="px-4 py-3 w-[15%] min-w-[100px]"></td>
                          <td className="px-4 py-3 w-[12%] min-w-[80px]"></td>
                          <td className="px-4 py-3 w-[15%] min-w-[110px]"></td>
                          <td className="px-4 py-3 w-[12%] min-w-[80px]"></td>
                          <td className="px-4 py-3 w-[16%] min-w-[120px]"></td>
                          <td className="px-4 py-3 w-[5%] min-w-[60px]"></td>
                        </tr>
                        
                        {/* Filas de transacciones */}
                        {player.transactions.map((transaction, transactionIndex) => {
                          const balance = calculateBalance(transaction.cantidad, transaction.operation_type)
                          
                          return (
                            <tr
                              key={`${player.id}-${transaction.id}`}
                              className="border-b border-gray-100 dark:border-gray-600 hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors bg-gray-50/50 dark:bg-gray-800/50"
                            >
                              <td className="px-4 py-3 w-[30%] min-w-[200px]">
                                <div className="pl-4 text-sm text-gray-500 dark:text-gray-400">
                                  ↳ Transacción {transactionIndex + 1}
                                </div>
                              </td>
                              <td className="px-4 py-3 w-[15%] min-w-[100px]">
                                <Input
                                  type="number"
                                  step="1000"
                                  placeholder="0"
                                  value={transaction.cantidad || ""}
                                  onChange={(e) =>
                                    updateTransaction(player.id, transaction.id, "cantidad", Number.parseFloat(e.target.value) || 0)
                                  }
                                  className="border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                              </td>
                              <td className="px-4 py-3 w-[12%] min-w-[80px]">
                                <div className="flex items-center gap-2">
                                  <span className={`text-sm font-medium ${transaction.operation_type === "CASH OUT" ? "text-red-600" : "text-gray-400"}`}>
                                    CASH OUT
                                  </span>
                                  <Switch
                                    checked={transaction.operation_type === "CASH IN"}
                                    onCheckedChange={(checked) =>
                                      updateTransaction(player.id, transaction.id, "operation_type", checked ? "CASH IN" : "CASH OUT")
                                    }
                                  />
                                  <span className={`text-sm font-medium ${transaction.operation_type === "CASH IN" ? "text-green-600" : "text-gray-400"}`}>
                                    CASH IN
                                  </span>
                                </div>
                              </td>
                              <td className="px-4 py-3 w-[15%] min-w-[110px]">
                                <select
                                  value={transaction.transaction_media}
                                  onChange={(e) =>
                                    updateTransaction(player.id, transaction.id, "transaction_media", e.target.value as "DIGITAL" | "CASH")
                                  }
                                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-800 dark:text-white"
                                >
                                  <option value="DIGITAL">Digital</option>
                                  <option value="CASH">Cash</option>
                                </select>
                              </td>
                              <td className="px-4 py-3 w-[12%] min-w-[80px]">
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
                              <td className="px-4 py-3 w-[16%] min-w-[120px]">
                                <Input
                                  placeholder="Comentarios de la Transacción"
                                  value={transaction.comment || ""}
                                  onChange={(e) => updateTransaction(player.id, transaction.id, "comment", e.target.value)}
                                  className="border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                />
                              </td>
                              <td className="px-4 py-3 text-center w-[5%] min-w-[60px]">
                                <Button
                                  onClick={() => removeTransactionFromPlayer(player.id, transaction.id)}
                                  variant="ghost"
                                  size="sm"
                                  className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </td>
                            </tr>
                          )
                        })}
                        
                        {/* Filas de bonos */}
                        {player.bonos.map((bono, bonoIndex) => {
                          return (
                            <tr
                              key={`${player.id}-bono-${bono.id}`}
                              className="border-b border-gray-100 dark:border-gray-600 hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors bg-green-50/30 dark:bg-green-900/10"
                            >
                              <td className="px-4 py-3 w-[30%] min-w-[200px]">
                                <div className="pl-4 text-sm font-medium text-green-600 dark:text-green-400">
                                  🎁 Bono {bonoIndex + 1}
                                </div>
                              </td>
                              <td className="px-4 py-3 w-[15%] min-w-[100px]">
                                <Input
                                  type="number"
                                  step="1000"
                                  placeholder="0"
                                  value={bono.value || ""}
                                  onChange={(e) =>
                                    updateBono(player.id, bono.id, "value", Number.parseFloat(e.target.value) || 0)
                                  }
                                  className="border-green-300 dark:border-green-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                                />
                              </td>
                              <td className="px-4 py-3 w-[12%] min-w-[80px]">
                                <span className="text-sm font-medium text-green-600 dark:text-green-400">
                                  BONO
                                </span>
                              </td>
                              <td className="px-4 py-3 w-[15%] min-w-[110px]">
                                <span className="text-sm text-gray-500">-</span>
                              </td>
                              <td className="px-4 py-3 w-[12%] min-w-[80px]">
                                <div className="px-3 py-2 rounded-lg font-medium text-sm bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                                  {formatCurrency(bono.value)}
                                </div>
                              </td>
                              <td className="px-4 py-3 w-[16%] min-w-[120px]">
                                <Input
                                  placeholder="Comentario del bono"
                                  value={bono.comment || ""}
                                  onChange={(e) => updateBono(player.id, bono.id, "comment", e.target.value)}
                                  className="border-green-300 dark:border-green-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                                />
                              </td>
                              <td className="px-4 py-3 text-center w-[5%] min-w-[60px]">
                                <Button
                                  onClick={() => removeBono(player.id, bono.id)}
                                  variant="ghost"
                                  size="sm"
                                  className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </td>
                            </tr>
                          )
                        })}
                        
                        {/* Filas de jackpots */}
                        {player.jackpots.map((jackpot, jackpotIndex) => {
                          return (
                            <tr
                              key={`${player.id}-jackpot-${jackpot.id}`}
                              className="border-b border-gray-100 dark:border-gray-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/20 transition-colors bg-yellow-50/30 dark:bg-yellow-900/10"
                            >
                              <td className="px-4 py-3 w-[30%] min-w-[200px]">
                                <div className="pl-4 text-sm font-medium text-yellow-600 dark:text-yellow-400">
                                  🏆 Jackpot {jackpotIndex + 1}
                                </div>
                              </td>
                              <td className="px-4 py-3 w-[15%] min-w-[100px]">
                                <Input
                                  type="number"
                                  step="1000"
                                  placeholder="0"
                                  value={jackpot.value || ""}
                                  onChange={(e) =>
                                    updateJackpot(player.id, jackpot.id, "value", Number.parseFloat(e.target.value) || 0)
                                  }
                                  className="border-yellow-300 dark:border-yellow-600 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
                                />
                              </td>
                              <td className="px-4 py-3 w-[12%] min-w-[80px]">
                                <span className="text-sm font-medium text-yellow-600 dark:text-yellow-400">
                                  JACKPOT
                                </span>
                              </td>
                              <td className="px-4 py-3 w-[15%] min-w-[110px]">
                                <Input
                                  placeholder="Mano ganadora"
                                  value={jackpot.winner_hand || ""}
                                  onChange={(e) => updateJackpot(player.id, jackpot.id, "winner_hand", e.target.value)}
                                  className="border-yellow-300 dark:border-yellow-600 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent text-sm"
                                />
                              </td>
                              <td className="px-4 py-3 w-[12%] min-w-[80px]">
                                <div className="px-3 py-2 rounded-lg font-medium text-sm bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
                                  {formatCurrency(jackpot.value)}
                                </div>
                              </td>
                              <td className="px-4 py-3 w-[16%] min-w-[120px]">
                                <Input
                                  placeholder="Comentario del jackpot"
                                  value={jackpot.comment || ""}
                                  onChange={(e) => updateJackpot(player.id, jackpot.id, "comment", e.target.value)}
                                  className="border-yellow-300 dark:border-yellow-600 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
                                />
                              </td>
                              <td className="px-4 py-3 text-center w-[5%] min-w-[60px]">
                                <Button
                                  onClick={() => removeJackpot(player.id, jackpot.id)}
                                  variant="ghost"
                                  size="sm"
                                  className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </td>
                            </tr>
                          )
                        })}
                      </React.Fragment>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
          )
        })()}

        {/* Player Summary - Solo mostrar si hay sesión activa */}
        {hasActiveSession && (
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
                    <Card key={player.id} className={`border-2 ${player.borderColor}`}>
                      <CardContent className="p-4">
                        <h3 className="font-semibold text-lg mb-2 text-gray-800 dark:text-white">{player.name}</h3>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600 dark:text-gray-400">Transacciones:</span>
                            <span className="font-medium">{totals.transactions}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-green-600 dark:text-green-400">Total Cash In:</span>
                            <span className="font-medium text-green-700 dark:text-green-300">
                              {formatCurrency(totals.cashIn)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-red-600 dark:text-red-400">Total Cash Out:</span>
                            <span className="font-medium text-red-700 dark:text-red-300">
                              {formatCurrency(totals.cashOut)}
                            </span>
                          </div>
                          {totals.bonos > 0 && (
                            <div className="flex justify-between">
                              <span className="text-green-600 dark:text-green-400">🎁 Bonos ({totals.bonos}):</span>
                              <span className="font-medium text-green-700 dark:text-green-300">
                                {formatCurrency(totals.bonosTotal)}
                              </span>
                            </div>
                          )}
                          {totals.jackpots > 0 && (
                            <div className="flex justify-between">
                              <span className="text-yellow-600 dark:text-yellow-400">🏆 Jackpots ({totals.jackpots}):</span>
                              <span className="font-medium text-yellow-700 dark:text-yellow-300">
                                {formatCurrency(totals.jackpotsTotal)}
                              </span>
                            </div>
                          )}
                          <div className="flex justify-between border-t pt-2">
                            <span className="text-blue-600 dark:text-blue-400 font-medium">Balance Total:</span>
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
        )}

        {/* Summary Section - Solo mostrar si hay sesión activa */}
        {hasActiveSession && (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6">
          <Card className="shadow-lg border-0 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20">
            <CardContent className="p-4 sm:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs sm:text-sm font-medium text-green-600 dark:text-green-400">Total Cash In</p>
                  <p className="text-xl sm:text-2xl font-bold text-green-800 dark:text-green-200 break-all">
                    {formatCurrency(grandTotals.cashIn)}
                  </p>
                </div>
                <TrendingUp className="w-6 h-6 sm:w-8 sm:h-8 text-green-500 shrink-0" />
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-lg border-0 bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20">
            <CardContent className="p-4 sm:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs sm:text-sm font-medium text-red-600 dark:text-red-400">Total Cash Out</p>
                  <p className="text-xl sm:text-2xl font-bold text-red-800 dark:text-red-200 break-all">
                    {formatCurrency(grandTotals.cashOut)}
                  </p>
                </div>
                <TrendingDown className="w-6 h-6 sm:w-8 sm:h-8 text-red-500 shrink-0" />
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
        )}

        {/* Modal para agregar bono */}
        <Dialog open={showBonoModal} onOpenChange={setShowBonoModal}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Agregar Bono</DialogTitle>
              <DialogDescription>
                Selecciona un jugador y especifica la cantidad y comentario del bono.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="player-select">Jugador</Label>
                <select
                  id="player-select"
                  value={selectedPlayerForBono || ""}
                  onChange={(e) => setSelectedPlayerForBono(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-800 dark:text-white"
                >
                  <option value="">Selecciona un jugador</option>
                  {players
                    .filter((p) => p.userId !== null)
                    .map((player) => (
                      <option key={player.id} value={player.userId!}>
                        {player.name}
                      </option>
                    ))}
                </select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="bono-amount">Cantidad del Bono</Label>
                <Input
                  id="bono-amount"
                  type="number"
                  step="1000"
                  placeholder="0"
                  value={bonoAmount || ""}
                  onChange={(e) => setBonoAmount(Number.parseFloat(e.target.value) || 0)}
                  className="border-gray-300 dark:border-gray-600"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="bono-comment">Comentario</Label>
                <Input
                  id="bono-comment"
                  placeholder="Comentario del bono (opcional)"
                  value={bonoComment}
                  onChange={(e) => setBonoComment(e.target.value)}
                  className="border-gray-300 dark:border-gray-600"
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setShowBonoModal(false)
                  setSelectedPlayerForBono(null)
                  setBonoAmount(0)
                  setBonoComment("")
                }}
              >
                Cancelar
              </Button>
              <Button
                onClick={addBono}
                disabled={!selectedPlayerForBono || bonoAmount <= 0}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                Agregar Bono
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Modal para agregar jackpot */}
        <Dialog open={showJackpotModal} onOpenChange={setShowJackpotModal}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Agregar Jackpot</DialogTitle>
              <DialogDescription>
                Selecciona un jugador y especifica la cantidad, mano ganadora y comentario del jackpot.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="jackpot-player-select">Jugador</Label>
                <select
                  id="jackpot-player-select"
                  value={selectedPlayerForBono || ""}
                  onChange={(e) => setSelectedPlayerForBono(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-800 dark:text-white"
                >
                  <option value="">Selecciona un jugador</option>
                  {players
                    .filter((p) => p.userId !== null)
                    .map((player) => (
                      <option key={player.id} value={player.userId!}>
                        {player.name}
                      </option>
                    ))}
                </select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="jackpot-amount">Cantidad del Jackpot</Label>
                <Input
                  id="jackpot-amount"
                  type="number"
                  step="1000"
                  placeholder="0"
                  value={jackpotAmount || ""}
                  onChange={(e) => setJackpotAmount(Number.parseFloat(e.target.value) || 0)}
                  className="border-gray-300 dark:border-gray-600"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="winner-hand">Mano Ganadora</Label>
                <Input
                  id="winner-hand"
                  placeholder="Ej: Royal Flush, Full House, etc."
                  value={winnerHand}
                  onChange={(e) => setWinnerHand(e.target.value)}
                  className="border-gray-300 dark:border-gray-600"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="jackpot-comment">Comentario</Label>
                <Input
                  id="jackpot-comment"
                  placeholder="Comentario del jackpot (opcional)"
                  value={jackpotComment}
                  onChange={(e) => setJackpotComment(e.target.value)}
                  className="border-gray-300 dark:border-gray-600"
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setShowJackpotModal(false)
                  setSelectedPlayerForBono(null)
                  setJackpotAmount(0)
                  setJackpotComment("")
                  setWinnerHand("")
                }}
              >
                Cancelar
              </Button>
              <Button
                onClick={addJackpot}
                disabled={!selectedPlayerForBono || !winnerHand}
                className="bg-yellow-600 hover:bg-yellow-700 text-white"
              >
                Agregar Jackpot
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

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
