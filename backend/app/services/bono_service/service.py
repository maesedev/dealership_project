"""
Servicio Bono - Orquestador de lógica de bonos.
Este servicio consume el dominio Bono pero no lo modifica.
Se encarga de la comunicación con la base de datos y orquestación de operaciones.
"""

from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from app.domains.bono.domain import BonoDomain, BonoDomainService
from app.infrastructure.database.connection import get_database
from app.shared.utils.timezone import now_bogota, bogota_to_utc


class BonoService:
    """
    Servicio de aplicación para Bono.
    Consume el dominio Bono y maneja la persistencia.
    """
    
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.bonos
        self.domain_service = BonoDomainService()
    
    async def create_bono(self, user_id: str, session_id: str, value: int,
                         comment: str = None) -> BonoDomain:
        """
        Crear un nuevo bono usando el dominio.
        """
        # Usar el servicio de dominio para crear el bono
        bono = self.domain_service.create_bono(
            user_id=user_id,
            session_id=session_id,
            value=value,
            comment=comment
        )
        
        # Convertir a diccionario para MongoDB
        bono_dict = bono.dict(exclude={"id"})
        bono_dict["created_at"] = bono.created_at
        bono_dict["updated_at"] = bono.updated_at
        
        # Insertar en la base de datos
        result = await self.collection.insert_one(bono_dict)
        
        # Actualizar el ID generado
        bono.id = str(result.inserted_id)
        
        return bono
    
    async def get_bono_by_id(self, bono_id: str) -> Optional[BonoDomain]:
        """
        Obtener un bono por ID.
        """
        bono_data = await self.collection.find_one({"_id": ObjectId(bono_id)})
        
        if bono_data:
            bono_data["id"] = str(bono_data["_id"])
            del bono_data["_id"]
            return BonoDomain(**bono_data)
        
        return None
    
    async def get_all_bonos(self, skip: int = 0, limit: int = 100) -> List[BonoDomain]:
        """
        Obtener todos los bonos con paginación.
        """
        cursor = self.collection.find().skip(skip).limit(limit).sort("created_at", -1)
        bonos = []
        
        async for bono_data in cursor:
            bono_data["id"] = str(bono_data["_id"])
            del bono_data["_id"]
            bonos.append(BonoDomain(**bono_data))
        
        return bonos
    
    async def get_bonos_by_user(self, user_id: str, skip: int = 0,
                               limit: int = 100) -> List[BonoDomain]:
        """
        Obtener bonos por usuario específico.
        """
        cursor = self.collection.find({"user_id": user_id}).skip(skip).limit(limit).sort("created_at", -1)
        bonos = []
        
        async for bono_data in cursor:
            bono_data["id"] = str(bono_data["_id"])
            del bono_data["_id"]
            bonos.append(BonoDomain(**bono_data))
        
        return bonos
    
    async def get_bonos_by_session(self, session_id: str, skip: int = 0,
                                  limit: int = 100) -> List[BonoDomain]:
        """
        Obtener bonos por sesión específica.
        """
        cursor = self.collection.find({"session_id": session_id}).skip(skip).limit(limit).sort("created_at", -1)
        bonos = []
        
        async for bono_data in cursor:
            bono_data["id"] = str(bono_data["_id"])
            del bono_data["_id"]
            bonos.append(BonoDomain(**bono_data))
        
        return bonos
    
    async def filter_bonos(self, user_id: str = None, session_id: str = None,
                          min_value: int = None, max_value: int = None,
                          date_from: datetime = None, date_to: datetime = None,
                          skip: int = 0, limit: int = 100) -> List[BonoDomain]:
        """
        Filtrar bonos con múltiples criterios.
        """
        filters = {}
        
        if user_id:
            filters["user_id"] = user_id
        if session_id:
            filters["session_id"] = session_id
        if min_value is not None or max_value is not None:
            filters["value"] = {}
            if min_value is not None:
                filters["value"]["$gte"] = min_value
            if max_value is not None:
                filters["value"]["$lte"] = max_value
        if date_from or date_to:
            filters["created_at"] = {}
            if date_from:
                filters["created_at"]["$gte"] = date_from
            if date_to:
                filters["created_at"]["$lte"] = date_to
        
        cursor = self.collection.find(filters).skip(skip).limit(limit).sort("created_at", -1)
        bonos = []
        
        async for bono_data in cursor:
            bono_data["id"] = str(bono_data["_id"])
            del bono_data["_id"]
            bonos.append(BonoDomain(**bono_data))
        
        return bonos
    
    async def update_bono(self, bono_id: str, **updates) -> Optional[BonoDomain]:
        """
        Actualizar un bono existente.
        """
        # Obtener el bono actual
        existing_bono = await self.get_bono_by_id(bono_id)
        
        if not existing_bono:
            return None
        
        # Actualizar campos
        for key, value in updates.items():
            if value is not None and hasattr(existing_bono, key):
                setattr(existing_bono, key, value)
        
        existing_bono.updated_at = bogota_to_utc(now_bogota())
        
        # Validar reglas de negocio
        errors = existing_bono.validate_business_rules()
        if errors:
            raise ValueError(f"Errores de validación: {'; '.join(errors)}")
        
        # Convertir a diccionario para actualización
        update_data = existing_bono.dict(exclude={"id", "created_at"})
        
        # Actualizar en la base de datos
        await self.collection.update_one(
            {"_id": ObjectId(bono_id)},
            {"$set": update_data}
        )
        
        return existing_bono
    
    async def delete_bono(self, bono_id: str) -> bool:
        """
        Eliminar un bono.
        """
        result = await self.collection.delete_one({"_id": ObjectId(bono_id)})
        return result.deleted_count > 0
    
    async def get_bono_stats(self) -> dict:
        """
        Obtener estadísticas de bonos.
        """
        total_bonos = await self.collection.count_documents({})
        
        # Calcular totales
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_value": {"$sum": "$value"},
                    "average_value": {"$avg": "$value"},
                    "max_value": {"$max": "$value"},
                    "min_value": {"$min": "$value"}
                }
            }
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(1)
        stats = result[0] if result else {
            "total_value": 0,
            "average_value": 0,
            "max_value": 0,
            "min_value": 0
        }
        
        # Encontrar bono máximo y mínimo
        max_bono_data = await self.collection.find_one(sort=[("value", -1)])
        min_bono_data = await self.collection.find_one(sort=[("value", 1)])
        
        max_bono = None
        min_bono = None
        
        if max_bono_data:
            max_bono = {
                "id": str(max_bono_data["_id"]),
                "value": max_bono_data["value"],
                "user_id": max_bono_data["user_id"],
                "session_id": max_bono_data["session_id"]
            }
        
        if min_bono_data:
            min_bono = {
                "id": str(min_bono_data["_id"]),
                "value": min_bono_data["value"],
                "user_id": min_bono_data["user_id"],
                "session_id": min_bono_data["session_id"]
            }
        
        # Estadísticas por usuario
        user_pipeline = [
            {
                "$group": {
                    "_id": "$user_id",
                    "count": {"$sum": 1},
                    "total_value": {"$sum": "$value"}
                }
            }
        ]
        
        user_stats = await self.collection.aggregate(user_pipeline).to_list(None)
        bonos_by_user = {stat["_id"]: {"count": stat["count"], "total_value": stat["total_value"]} 
                        for stat in user_stats}
        
        # Estadísticas por sesión
        session_pipeline = [
            {
                "$group": {
                    "_id": "$session_id",
                    "count": {"$sum": 1},
                    "total_value": {"$sum": "$value"}
                }
            }
        ]
        
        session_stats = await self.collection.aggregate(session_pipeline).to_list(None)
        bonos_by_session = {stat["_id"]: {"count": stat["count"], "total_value": stat["total_value"]} 
                           for stat in session_stats}
        
        return {
            "total_bonos": total_bonos,
            "total_value": stats["total_value"],
            "average_value": round(stats["average_value"], 2),
            "max_bono": max_bono,
            "min_bono": min_bono,
            "bonos_by_user": bonos_by_user,
            "bonos_by_session": bonos_by_session
        }
    
    async def get_user_total_bonos(self, user_id: str) -> int:
        """
        Obtener el total de bonos de un usuario.
        """
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": None, "total": {"$sum": "$value"}}}
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(1)
        return result[0]["total"] if result else 0
    
    async def get_session_total_bonos(self, session_id: str) -> int:
        """
        Obtener el total de bonos de una sesión.
        """
        pipeline = [
            {"$match": {"session_id": session_id}},
            {"$group": {"_id": None, "total": {"$sum": "$value"}}}
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(1)
        return result[0]["total"] if result else 0

