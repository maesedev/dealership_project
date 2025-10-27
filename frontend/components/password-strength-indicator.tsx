"use client"

import { useState, useEffect } from 'react'
import { validatePassword, getPasswordStrength, PasswordValidation } from '@/lib/password-validator'
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react'

interface PasswordStrengthIndicatorProps {
  password: string
  showValidation?: boolean
}

export function PasswordStrengthIndicator({ password, showValidation = true }: PasswordStrengthIndicatorProps) {
  const [validation, setValidation] = useState<PasswordValidation>({
    isValid: false,
    errors: [],
    checks: {
      minLength: false,
      hasUppercase: false,
      hasLowercase: false,
      hasNumber: false,
    }
  })

  useEffect(() => {
    if (password) {
      setValidation(validatePassword(password))
    } else {
      setValidation({
        isValid: false,
        errors: [],
        checks: {
          minLength: false,
          hasUppercase: false,
          hasLowercase: false,
          hasNumber: false,
        }
      })
    }
  }, [password])

  if (!password || !showValidation) {
    return null
  }

  const strength = getPasswordStrength(password)
  const strengthColors = {
    weak: 'bg-red-500',
    medium: 'bg-yellow-500',
    strong: 'bg-green-500'
  }

  const strengthLabels = {
    weak: 'Débil',
    medium: 'Media',
    strong: 'Fuerte'
  }

  return (
    <div className="space-y-3">
      {/* Barra de fortaleza */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">Fortaleza de la contraseña:</span>
          <span className={`font-medium ${
            strength === 'weak' ? 'text-red-600' : 
            strength === 'medium' ? 'text-yellow-600' : 
            'text-green-600'
          }`}>
            {strengthLabels[strength]}
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-300 ${strengthColors[strength]}`}
            style={{ 
              width: strength === 'weak' ? '25%' : 
                     strength === 'medium' ? '60%' : 
                     '100%' 
            }}
          />
        </div>
      </div>

      {/* Lista de validaciones */}
      <div className="space-y-1">
        <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Requisitos de la contraseña:
        </div>
        <div className="space-y-1">
          <ValidationItem 
            isValid={validation.checks.minLength}
            text="Al menos 8 caracteres"
          />
          <ValidationItem 
            isValid={validation.checks.hasUppercase}
            text="Al menos una letra mayúscula"
          />
          <ValidationItem 
            isValid={validation.checks.hasLowercase}
            text="Al menos una letra minúscula"
          />
          <ValidationItem 
            isValid={validation.checks.hasNumber}
            text="Al menos un número"
          />
        </div>
      </div>

      {/* Errores */}
      {validation.errors.length > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
            <div className="space-y-1">
              {validation.errors.map((error, index) => (
                <div key={index} className="text-sm text-red-800 dark:text-red-200">
                  • {error}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

interface ValidationItemProps {
  isValid: boolean
  text: string
}

function ValidationItem({ isValid, text }: ValidationItemProps) {
  return (
    <div className="flex items-center gap-2 text-sm">
      {isValid ? (
        <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />
      ) : (
        <XCircle className="h-4 w-4 text-gray-400 flex-shrink-0" />
      )}
      <span className={isValid ? 'text-green-700 dark:text-green-300' : 'text-gray-500 dark:text-gray-400'}>
        {text}
      </span>
    </div>
  )
}
