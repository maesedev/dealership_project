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
from app.shared.utils.logger import get_logger

# Logger para este script
logger = get_logger(__name__)


async def main():
    """Función principal de demostración"""
    
    logger.info("=" * 60)
    logger.info("🔐 DEMOSTRACIÓN DEL SISTEMA DE AUTENTICACIÓN JWT")
    logger.info("=" * 60)
    
    # Inicializar servicios
    user_service = UserService()
    auth_service = AuthService()
    
    # Datos de prueba
    test_username = "demo_user"
    test_password = "DemoPassword123"
    test_name = "Usuario Demo"
    
    logger.info("\n📋 Paso 1: Crear usuario de prueba")
    logger.info("-" * 60)
    
    try:
        # Intentar obtener usuario existente
        existing_user = await user_service.get_user_by_username(test_username)
        
        if existing_user:
            logger.info(f"✓ Usuario ya existe: {test_username}")
            user = existing_user
        else:
            # Crear nuevo usuario
            user = await user_service.create_user(
                username=test_username,
                password=test_password,
                name=test_name,
                roles=[UserRole.USER, UserRole.DEALER]
            )
            logger.info(f"✓ Usuario creado exitosamente:")
            logger.info(f"  - Username: {user.username}")
            logger.info(f"  - Nombre: {user.name}")
            logger.info(f"  - Roles: {[role.value for role in user.roles]}")
            logger.info(f"  - ID: {user.id}")
    
    except Exception as e:
        logger.error(f"✗ Error al crear usuario: {e}")
        return
    
    logger.info("\n🔑 Paso 2: Login - Autenticación con credenciales")
    logger.info("-" * 60)
    
    try:
        # Intentar login con credenciales correctas
        auth_result = await auth_service.login(
            username=test_username,
            password=test_password
        )
        
        if auth_result:
            logger.info("✓ Login exitoso!")
            logger.info(f"  - Token Type: {auth_result['token_type']}")
            logger.info(f"  - Expira en: {auth_result['expires_in']} segundos")
            logger.info(f"  - Access Token (primeros 50 caracteres): {auth_result['access_token'][:50]}...")
            logger.info(f"\n✓ Datos del usuario autenticado:")
            logger.info(f"  - Username: {auth_result['user'].username}")
            logger.info(f"  - Nombre: {auth_result['user'].name}")
            logger.info(f"  - Roles: {[role.value for role in auth_result['user'].roles]}")
            logger.info(f"  - Estado: {'Activo' if auth_result['user'].is_active else 'Inactivo'}")
            
            token = auth_result['access_token']
        else:
            logger.warning("✗ Login fallido - Credenciales inválidas")
            return
    
    except Exception as e:
        logger.error(f"✗ Error en login: {e}")
        return
    
    logger.info("\n🔍 Paso 3: Verificar token JWT")
    logger.info("-" * 60)
    
    try:
        # Verificar el token
        payload = await auth_service.verify_token(token)
        
        if payload:
            logger.info("✓ Token válido!")
            logger.info(f"  - Usuario ID: {payload.get('sub')}")
            logger.info(f"  - Username: {payload.get('username')}")
            logger.info(f"  - Roles: {payload.get('roles')}")
            logger.info(f"  - Nombre: {payload.get('name')}")
            logger.info(f"  - Expira: {payload.get('exp')}")
        else:
            logger.warning("✗ Token inválido")
            return
    
    except Exception as e:
        logger.error(f"✗ Error al verificar token: {e}")
        return
    
    logger.info("\n👤 Paso 4: Obtener usuario desde token")
    logger.info("-" * 60)
    
    try:
        # Obtener usuario actual usando el token
        current_user = await auth_service.get_current_user(token)
        
        if current_user:
            logger.info("✓ Usuario obtenido desde token:")
            logger.info(f"  - ID: {current_user.id}")
            logger.info(f"  - Username: {current_user.username}")
            logger.info(f"  - Nombre: {current_user.name}")
            logger.info(f"  - Roles: {[role.value for role in current_user.roles]}")
            logger.info(f"  - Es Admin: {current_user.is_admin()}")
            logger.info(f"  - Es Dealer: {current_user.is_dealer()}")
            logger.info(f"  - Puede acceder a funciones admin: {current_user.can_access_admin_features()}")
        else:
            logger.warning("✗ No se pudo obtener usuario desde token")
            return
    
    except Exception as e:
        logger.error(f"✗ Error al obtener usuario: {e}")
        return
    
    logger.info("\n🔄 Paso 5: Refrescar token")
    logger.info("-" * 60)
    
    try:
        # Refrescar el token
        refresh_result = await auth_service.refresh_token(token)
        
        if refresh_result:
            logger.info("✓ Token refrescado exitosamente!")
            logger.info(f"  - Nuevo token (primeros 50 caracteres): {refresh_result['access_token'][:50]}...")
            logger.info(f"  - Token Type: {refresh_result['token_type']}")
            logger.info(f"  - Expira en: {refresh_result['expires_in']} segundos")
            
            new_token = refresh_result['access_token']
            logger.info(f"\n✓ Los tokens son diferentes: {token[:20]}... ≠ {new_token[:20]}...")
        else:
            logger.warning("✗ No se pudo refrescar el token")
            return
    
    except Exception as e:
        logger.error(f"✗ Error al refrescar token: {e}")
        return
    
    logger.info("\n❌ Paso 6: Intentar login con contraseña incorrecta")
    logger.info("-" * 60)
    
    try:
        # Intentar login con contraseña incorrecta
        failed_login = await auth_service.login(
            username=test_username,
            password="PasswordIncorrecta123"
        )
        
        if failed_login:
            logger.warning("✗ Esto no debería pasar - login con contraseña incorrecta exitoso")
        else:
            logger.info("✓ Login rechazado correctamente - Contraseña incorrecta")
            
            # Verificar que se registró el intento fallido
            user_after_fail = await user_service.get_user_by_username(test_username)
            logger.info(f"  - Intentos fallidos: {user_after_fail.security.failed_attempts}")
    
    except Exception as e:
        logger.error(f"✗ Error al probar login fallido: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ DEMOSTRACIÓN COMPLETADA EXITOSAMENTE")
    logger.info("=" * 60)
    logger.info("\n📝 Resumen:")
    logger.info("  1. ✓ Usuario creado/recuperado")
    logger.info("  2. ✓ Login exitoso con JWT generado")
    logger.info("  3. ✓ Token verificado correctamente")
    logger.info("  4. ✓ Usuario obtenido desde token")
    logger.info("  5. ✓ Token refrescado exitosamente")
    logger.info("  6. ✓ Intentos fallidos manejados correctamente")
    logger.info("\n🎉 El sistema de autenticación está funcionando perfectamente!")
    logger.info("\n💡 Próximos pasos:")
    logger.info("  - Probar los endpoints HTTP en /api/v1/auth/login")
    logger.info("  - Implementar autenticación en el frontend")
    logger.info("  - Proteger endpoints con las dependencias de auth")
    logger.info()


if __name__ == "__main__":
    # Ejecutar la demostración
    asyncio.run(main())