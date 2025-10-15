"""
Ejemplo de cómo crear endpoints protegidos con autenticación JWT.

Este archivo muestra diferentes formas de proteger endpoints usando
las dependencias de autenticación.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.shared.dependencies.auth import (
    get_current_user,
    get_current_active_user,
    require_admin,
    require_dealer,
    require_manager,
    RoleChecker
)
from app.domains.user.domain import UserDomain, UserRole

# Crear router de ejemplo
router = APIRouter(prefix="/example", tags=["examples"])


# ============================================================================
# EJEMPLO 1: Endpoint básico protegido (requiere autenticación)
# ============================================================================

@router.get("/profile")
async def get_profile(current_user: UserDomain = Depends(get_current_active_user)):
    """
    Endpoint que requiere autenticación básica.
    
    Cualquier usuario autenticado y activo puede acceder.
    
    Para probar:
        curl -X GET "http://localhost:8000/api/v1/example/profile" \
             -H "Authorization: Bearer {tu_token}"
    """
    return {
        "message": f"Hola {current_user.name}!",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "name": current_user.name,
            "roles": [role.value for role in current_user.roles]
        }
    }


# ============================================================================
# EJEMPLO 2: Endpoint solo para administradores
# ============================================================================

@router.get("/admin-only", dependencies=[Depends(require_admin)])
async def admin_only_endpoint():
    """
    Endpoint solo para administradores.
    
    Solo usuarios con rol ADMIN pueden acceder.
    
    Para probar:
        curl -X GET "http://localhost:8000/api/v1/example/admin-only" \
             -H "Authorization: Bearer {token_de_admin}"
    """
    return {
        "message": "¡Bienvenido, administrador!",
        "info": "Este endpoint está protegido solo para admins"
    }


# ============================================================================
# EJEMPLO 3: Endpoint para dealers (dealers y admins)
# ============================================================================

@router.post("/create-sale", dependencies=[Depends(require_dealer)])
async def create_sale(sale_data: dict):
    """
    Endpoint para crear ventas.
    
    Solo usuarios con rol DEALER o ADMIN pueden acceder.
    
    Para probar:
        curl -X POST "http://localhost:8000/api/v1/example/create-sale" \
             -H "Authorization: Bearer {token_dealer}" \
             -H "Content-Type: application/json" \
             -d '{"vehicle_id": "123", "customer_id": "456", "price": 25000}'
    """
    return {
        "message": "Venta creada exitosamente",
        "sale": sale_data
    }


# ============================================================================
# EJEMPLO 4: Endpoint con roles personalizados
# ============================================================================

# Crear dependencia personalizada para dealers y managers
require_sales_team = RoleChecker([UserRole.DEALER, UserRole.MANAGER])

@router.get("/sales-report", dependencies=[Depends(require_sales_team)])
async def get_sales_report():
    """
    Endpoint para reportes de ventas.
    
    Solo usuarios con rol DEALER o MANAGER pueden acceder.
    
    Para probar:
        curl -X GET "http://localhost:8000/api/v1/example/sales-report" \
             -H "Authorization: Bearer {token}"
    """
    return {
        "message": "Reporte de ventas",
        "sales": [
            {"id": "1", "vehicle": "Honda Civic", "price": 25000},
            {"id": "2", "vehicle": "Toyota Corolla", "price": 23000}
        ]
    }


# ============================================================================
# EJEMPLO 5: Endpoint con lógica condicional basada en roles
# ============================================================================

@router.get("/dashboard")
async def get_dashboard(current_user: UserDomain = Depends(get_current_active_user)):
    """
    Endpoint que devuelve diferentes datos según el rol del usuario.
    
    El contenido del dashboard cambia según el rol.
    
    Para probar:
        curl -X GET "http://localhost:8000/api/v1/example/dashboard" \
             -H "Authorization: Bearer {token}"
    """
    dashboard_data = {
        "user": current_user.name,
        "role": [role.value for role in current_user.roles]
    }
    
    # Datos específicos según el rol
    if current_user.is_admin():
        dashboard_data["admin_data"] = {
            "total_users": 150,
            "total_sales": 45,
            "revenue": 1250000,
            "permissions": ["all"]
        }
    elif current_user.is_dealer():
        dashboard_data["dealer_data"] = {
            "my_sales": 12,
            "my_revenue": 350000,
            "commission": 15000,
            "permissions": ["create_sale", "view_inventory"]
        }
    elif current_user.is_manager():
        dashboard_data["manager_data"] = {
            "team_sales": 30,
            "team_revenue": 850000,
            "team_members": 8,
            "permissions": ["view_reports", "manage_team"]
        }
    else:
        dashboard_data["user_data"] = {
            "favorites": 5,
            "viewed_vehicles": 23,
            "permissions": ["view_vehicles", "contact_dealer"]
        }
    
    return dashboard_data


# ============================================================================
# EJEMPLO 6: Endpoint con verificación manual de permisos
# ============================================================================

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: UserDomain = Depends(get_current_active_user)
):
    """
    Endpoint para eliminar usuarios.
    
    - Admins pueden eliminar cualquier usuario
    - Usuarios normales solo pueden eliminar su propia cuenta
    
    Para probar:
        curl -X DELETE "http://localhost:8000/api/v1/example/users/123" \
             -H "Authorization: Bearer {token}"
    """
    # Verificar permisos
    if not current_user.is_admin() and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar este usuario"
        )
    
    # Lógica de eliminación aquí...
    return {
        "message": f"Usuario {user_id} eliminado exitosamente",
        "deleted_by": current_user.username
    }


# ============================================================================
# EJEMPLO 7: Endpoint con múltiples niveles de verificación
# ============================================================================

@router.put("/settings/system")
async def update_system_settings(
    settings: dict,
    current_user: UserDomain = Depends(get_current_active_user)
):
    """
    Endpoint para actualizar configuración del sistema.
    
    Requiere múltiples verificaciones:
    1. Usuario autenticado
    2. Usuario activo
    3. Rol de administrador
    4. Verificación adicional personalizada
    
    Para probar:
        curl -X PUT "http://localhost:8000/api/v1/example/settings/system" \
             -H "Authorization: Bearer {token_admin}" \
             -H "Content-Type: application/json" \
             -d '{"max_users": 1000, "maintenance_mode": false}'
    """
    # Verificar que es admin
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden modificar configuración del sistema"
        )
    
    # Verificaciones adicionales personalizadas
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario no activo"
        )
    
    # Verificar que no esté bloqueado
    if current_user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta bloqueada"
        )
    
    # Actualizar configuración aquí...
    return {
        "message": "Configuración actualizada exitosamente",
        "settings": settings,
        "updated_by": current_user.username
    }


# ============================================================================
# RESUMEN DE USO
# ============================================================================

"""
RESUMEN DE PATRONES DE PROTECCIÓN:

1. Autenticación básica:
   async def endpoint(user: UserDomain = Depends(get_current_active_user))

2. Solo admins:
   @router.get("/...", dependencies=[Depends(require_admin)])

3. Dealers o admins:
   @router.get("/...", dependencies=[Depends(require_dealer)])

4. Managers o admins:
   @router.get("/...", dependencies=[Depends(require_manager)])

5. Roles personalizados:
   checker = RoleChecker([UserRole.CUSTOM1, UserRole.CUSTOM2])
   @router.get("/...", dependencies=[Depends(checker)])

6. Lógica condicional:
   if current_user.is_admin():
       # hacer algo
   elif current_user.is_dealer():
       # hacer otra cosa

7. Verificación manual:
   if not current_user.has_permission():
       raise HTTPException(status_code=403, detail="Sin permisos")
"""

