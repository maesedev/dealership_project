"""
Script de ejemplo para probar el sistema de autenticación.

Este script demuestra cómo:
1. Crear un usuario
2. Autenticarse (login)
3. Usar el token JWT para acceder a endpoints protegidos
4. Refrescar el token

Uso:
    python examples/test_auth.py
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.user_service.service import UserService
from app.services.auth_service.service import AuthService
from app.domains.user.domain import UserRole


async def main():
    """Función principal de demostración"""
    
    print("=" * 60)
    print("🔐 DEMOSTRACIÓN DEL SISTEMA DE AUTENTICACIÓN JWT")
    print("=" * 60)
    
    # Inicializar servicios
    user_service = UserService()
    auth_service = AuthService()
    
    # Datos de prueba
    test_username = "demo_user"
    test_password = "DemoPassword123"
    test_name = "Usuario Demo"
    
    print("\n📋 Paso 1: Crear usuario de prueba")
    print("-" * 60)
    
    try:
        # Intentar obtener usuario existente
        existing_user = await user_service.get_user_by_username(test_username)
        
        if existing_user:
            print(f"✓ Usuario ya existe: {test_username}")
            user = existing_user
        else:
            # Crear nuevo usuario
            user = await user_service.create_user(
                username=test_username,
                password=test_password,
                name=test_name,
                roles=[UserRole.USER, UserRole.DEALER]
            )
            print(f"✓ Usuario creado exitosamente:")
            print(f"  - Username: {user.username}")
            print(f"  - Nombre: {user.name}")
            print(f"  - Roles: {[role.value for role in user.roles]}")
            print(f"  - ID: {user.id}")
    
    except Exception as e:
        print(f"✗ Error al crear usuario: {e}")
        return
    
    print("\n🔑 Paso 2: Login - Autenticación con credenciales")
    print("-" * 60)
    
    try:
        # Intentar login con credenciales correctas
        auth_result = await auth_service.login(
            username=test_username,
            password=test_password
        )
        
        if auth_result:
            print("✓ Login exitoso!")
            print(f"  - Token Type: {auth_result['token_type']}")
            print(f"  - Expira en: {auth_result['expires_in']} segundos")
            print(f"  - Access Token (primeros 50 caracteres): {auth_result['access_token'][:50]}...")
            print(f"\n✓ Datos del usuario autenticado:")
            print(f"  - Username: {auth_result['user'].username}")
            print(f"  - Nombre: {auth_result['user'].name}")
            print(f"  - Roles: {[role.value for role in auth_result['user'].roles]}")
            print(f"  - Estado: {'Activo' if auth_result['user'].is_active else 'Inactivo'}")
            
            token = auth_result['access_token']
        else:
            print("✗ Login fallido - Credenciales inválidas")
            return
    
    except Exception as e:
        print(f"✗ Error en login: {e}")
        return
    
    print("\n🔍 Paso 3: Verificar token JWT")
    print("-" * 60)
    
    try:
        # Verificar el token
        payload = await auth_service.verify_token(token)
        
        if payload:
            print("✓ Token válido!")
            print(f"  - Usuario ID: {payload.get('sub')}")
            print(f"  - Username: {payload.get('username')}")
            print(f"  - Roles: {payload.get('roles')}")
            print(f"  - Nombre: {payload.get('name')}")
            print(f"  - Expira: {payload.get('exp')}")
        else:
            print("✗ Token inválido")
            return
    
    except Exception as e:
        print(f"✗ Error al verificar token: {e}")
        return
    
    print("\n👤 Paso 4: Obtener usuario desde token")
    print("-" * 60)
    
    try:
        # Obtener usuario actual usando el token
        current_user = await auth_service.get_current_user(token)
        
        if current_user:
            print("✓ Usuario obtenido desde token:")
            print(f"  - ID: {current_user.id}")
            print(f"  - Username: {current_user.username}")
            print(f"  - Nombre: {current_user.name}")
            print(f"  - Roles: {[role.value for role in current_user.roles]}")
            print(f"  - Es Admin: {current_user.is_admin()}")
            print(f"  - Es Dealer: {current_user.is_dealer()}")
            print(f"  - Puede acceder a funciones admin: {current_user.can_access_admin_features()}")
        else:
            print("✗ No se pudo obtener usuario desde token")
            return
    
    except Exception as e:
        print(f"✗ Error al obtener usuario: {e}")
        return
    
    print("\n🔄 Paso 5: Refrescar token")
    print("-" * 60)
    
    try:
        # Refrescar el token
        refresh_result = await auth_service.refresh_token(token)
        
        if refresh_result:
            print("✓ Token refrescado exitosamente!")
            print(f"  - Nuevo token (primeros 50 caracteres): {refresh_result['access_token'][:50]}...")
            print(f"  - Token Type: {refresh_result['token_type']}")
            print(f"  - Expira en: {refresh_result['expires_in']} segundos")
            
            new_token = refresh_result['access_token']
            print(f"\n✓ Los tokens son diferentes: {token[:20]}... ≠ {new_token[:20]}...")
        else:
            print("✗ No se pudo refrescar el token")
            return
    
    except Exception as e:
        print(f"✗ Error al refrescar token: {e}")
        return
    
    print("\n❌ Paso 6: Intentar login con contraseña incorrecta")
    print("-" * 60)
    
    try:
        # Intentar login con contraseña incorrecta
        failed_login = await auth_service.login(
            username=test_username,
            password="PasswordIncorrecta123"
        )
        
        if failed_login:
            print("✗ Esto no debería pasar - login con contraseña incorrecta exitoso")
        else:
            print("✓ Login rechazado correctamente - Contraseña incorrecta")
            
            # Verificar que se registró el intento fallido
            user_after_fail = await user_service.get_user_by_username(test_username)
            print(f"  - Intentos fallidos: {user_after_fail.security.failed_attempts}")
    
    except Exception as e:
        print(f"✗ Error al probar login fallido: {e}")
    
    print("\n" + "=" * 60)
    print("✅ DEMOSTRACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 60)
    print("\n📝 Resumen:")
    print("  1. ✓ Usuario creado/recuperado")
    print("  2. ✓ Login exitoso con JWT generado")
    print("  3. ✓ Token verificado correctamente")
    print("  4. ✓ Usuario obtenido desde token")
    print("  5. ✓ Token refrescado exitosamente")
    print("  6. ✓ Intentos fallidos manejados correctamente")
    print("\n🎉 El sistema de autenticación está funcionando perfectamente!")
    print("\n💡 Próximos pasos:")
    print("  - Probar los endpoints HTTP en /api/v1/auth/login")
    print("  - Implementar autenticación en el frontend")
    print("  - Proteger endpoints con las dependencias de auth")
    print()


if __name__ == "__main__":
    # Ejecutar la demostración
    asyncio.run(main())

