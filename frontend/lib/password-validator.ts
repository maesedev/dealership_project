/**
 * Validador de contraseñas para el frontend
 * Implementa las mismas validaciones que el backend
 */

export interface PasswordValidation {
  isValid: boolean
  errors: string[]
  checks: {
    minLength: boolean
    hasUppercase: boolean
    hasLowercase: boolean
    hasNumber: boolean
  }
}

export function validatePassword(password: string): PasswordValidation {
  const errors: string[] = []
  
  // Si la contraseña está vacía, es válida (para usuarios tipo USER)
  if (!password || password === '') {
    return {
      isValid: true,
      errors: [],
      checks: {
        minLength: false,
        hasUppercase: false,
        hasLowercase: false,
        hasNumber: false,
      }
    }
  }
  
  const checks = {
    minLength: password.length >= 8,
    hasUppercase: /[A-Z]/.test(password),
    hasLowercase: /[a-z]/.test(password),
    hasNumber: /\d/.test(password),
  }

  // Validar longitud mínima
  if (!checks.minLength) {
    errors.push('La contraseña debe tener al menos 8 caracteres')
  }

  // Validar mayúscula
  if (!checks.hasUppercase) {
    errors.push('La contraseña debe contener al menos una letra mayúscula')
  }

  // Validar minúscula
  if (!checks.hasLowercase) {
    errors.push('La contraseña debe contener al menos una letra minúscula')
  }

  // Validar número
  if (!checks.hasNumber) {
    errors.push('La contraseña debe contener al menos un número')
  }

  return {
    isValid: errors.length === 0,
    errors,
    checks,
  }
}

export function getPasswordStrength(password: string): 'weak' | 'medium' | 'strong' {
  const validation = validatePassword(password)
  
  if (!validation.isValid) {
    return 'weak'
  }

  const { checks } = validation
  const validChecks = Object.values(checks).filter(Boolean).length

  if (validChecks === 4) {
    return 'strong'
  } else if (validChecks >= 3) {
    return 'medium'
  } else {
    return 'weak'
  }
}
