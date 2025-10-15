"""
Servicio JackpotPrice - Orquestador de lógica de premios de jackpot.
Este servicio consume el dominio JackpotPrice pero no lo modifica.
Se encarga de la comunicación con la base de datos y orquestación de operaciones.
"""

from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from app.domains.jackpot_price.domain import JackpotPriceDomain, JackpotPriceDomainService
from app.infrastructure.database.connection import get_database


class JackpotPriceService:
    """
    Servicio de aplicación para JackpotPrice.
    Consume el dominio JackpotPrice y maneja la persistencia.
    """
    
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.jackpot_prices
        self.domain_service = JackpotPriceDomainService()
    
    async def create_jackpot_price(self, user_id: str, session_id: str, value: int,
                                  winner_hand: str = None, comment: str = None) -> JackpotPriceDomain:
        """
        Crear un nuevo premio de jackpot usando el dominio.
        """
        # Usar el servicio de dominio para crear el jackpot
        jackpot_price = self.domain_service.create_jackpot_price(
            user_id=user_id,
            session_id=session_id,
            value=value,
            winner_hand=winner_hand,
            comment=comment
        )
        
        # Convertir a diccionario para MongoDB
        jackpot_dict = jackpot_price.dict(exclude={"id"})
        jackpot_dict["created_at"] = jackpot_price.created_at
        jackpot_dict["updated_at"] = jackpot_price.updated_at
        
        # Insertar en la base de datos
        result = await self.collection.insert_one(jackpot_dict)
        
        # Actualizar el ID generado
        jackpot_price.id = str(result.inserted_id)
        
        return jackpot_price
    
    async def get_jackpot_by_id(self, jackpot_id: str) -> Optional[JackpotPriceDomain]:
        """
        Obtener un premio de jackpot por ID.
        """
        jackpot_data = await self.collection.find_one({"_id": ObjectId(jackpot_id)})
        
        if jackpot_data:
            jackpot_data["id"] = str(jackpot_data["_id"])
            del jackpot_data["_id"]
            return JackpotPriceDomain(**jackpot_data)
        
        return None
    
    async def get_all_jackpots(self, skip: int = 0, limit: int = 100) -> List[JackpotPriceDomain]:
        """
        Obtener todos los premios de jackpot con paginación.
        """
        cursor = self.collection.find().skip(skip).limit(limit).sort("created_at", -1)
        jackpots = []
        
        async for jackpot_data in cursor:
            jackpot_data["id"] = str(jackpot_data["_id"])
            del jackpot_data["_id"]
            jackpots.append(JackpotPriceDomain(**jackpot_data))
        
        return jackpots
    
    async def get_jackpots_by_user(self, user_id: str, skip: int = 0,
                                  limit: int = 100) -> List[JackpotPriceDomain]:
        """
        Obtener premios de jackpot por usuario específico.
        """
        cursor = self.collection.find({"user_id": user_id}).skip(skip).limit(limit).sort("created_at", -1)
        jackpots = []
        
        async for jackpot_data in cursor:
            jackpot_data["id"] = str(jackpot_data["_id"])
            del jackpot_data["_id"]
            jackpots.append(JackpotPriceDomain(**jackpot_data))
        
        return jackpots
    
    async def get_jackpots_by_session(self, session_id: str, skip: int = 0,
                                     limit: int = 100) -> List[JackpotPriceDomain]:
        """
        Obtener premios de jackpot por sesión específica.
        """
        cursor = self.collection.find({"session_id": session_id}).skip(skip).limit(limit).sort("created_at", -1)
        jackpots = []
        
        async for jackpot_data in cursor:
            jackpot_data["id"] = str(jackpot_data["_id"])
            del jackpot_data["_id"]
            jackpots.append(JackpotPriceDomain(**jackpot_data))
        
        return jackpots
    
    async def get_high_value_jackpots(self, threshold: int = 10000, 
                                     skip: int = 0, limit: int = 100) -> List[JackpotPriceDomain]:
        """
        Obtener premios de jackpot de alto valor.
        """
        cursor = self.collection.find({"value": {"$gte": threshold}}).skip(skip).limit(limit).sort("value", -1)
        jackpots = []
        
        async for jackpot_data in cursor:
            jackpot_data["id"] = str(jackpot_data["_id"])
            del jackpot_data["_id"]
            jackpots.append(JackpotPriceDomain(**jackpot_data))
        
        return jackpots
    
    async def filter_jackpots(self, user_id: str = None, session_id: str = None,
                             min_value: int = None, max_value: int = None,
                             winner_hand: str = None, date_from: datetime = None,
                             date_to: datetime = None, skip: int = 0, 
                             limit: int = 100) -> List[JackpotPriceDomain]:
        """
        Filtrar premios de jackpot con múltiples criterios.
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
        if winner_hand:
            filters["winner_hand"] = {"$regex": winner_hand, "$options": "i"}
        if date_from or date_to:
            filters["created_at"] = {}
            if date_from:
                filters["created_at"]["$gte"] = date_from
            if date_to:
                filters["created_at"]["$lte"] = date_to
        
        cursor = self.collection.find(filters).skip(skip).limit(limit).sort("created_at", -1)
        jackpots = []
        
        async for jackpot_data in cursor:
            jackpot_data["id"] = str(jackpot_data["_id"])
            del jackpot_data["_id"]
            jackpots.append(JackpotPriceDomain(**jackpot_data))
        
        return jackpots
    
    async def update_jackpot(self, jackpot_id: str, **updates) -> Optional[JackpotPriceDomain]:
        """
        Actualizar un premio de jackpot existente.
        """
        # Obtener el jackpot actual
        existing_jackpot = await self.get_jackpot_by_id(jackpot_id)
        
        if not existing_jackpot:
            return None
        
        # Actualizar campos
        for key, value in updates.items():
            if value is not None and hasattr(existing_jackpot, key):
                setattr(existing_jackpot, key, value)
        
        existing_jackpot.updated_at = datetime.now(timezone.utc)
        
        # Validar reglas de negocio
        errors = existing_jackpot.validate_business_rules()
        if errors:
            raise ValueError(f"Errores de validación: {'; '.join(errors)}")
        
        # Convertir a diccionario para actualización
        update_data = existing_jackpot.dict(exclude={"id", "created_at"})
        
        # Actualizar en la base de datos
        await self.collection.update_one(
            {"_id": ObjectId(jackpot_id)},
            {"$set": update_data}
        )
        
        return existing_jackpot
    
    async def delete_jackpot(self, jackpot_id: str) -> bool:
        """
        Eliminar un premio de jackpot.
        """
        result = await self.collection.delete_one({"_id": ObjectId(jackpot_id)})
        return result.deleted_count > 0
    
    async def get_jackpot_stats(self) -> dict:
        """
        Obtener estadísticas de premios de jackpot.
        """
        total_jackpots = await self.collection.count_documents({})
        
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
        
        # Contar jackpots de alto valor
        high_value_count = await self.collection.count_documents({"value": {"$gte": 10000}})
        
        # Encontrar jackpot máximo y mínimo
        max_jackpot_data = await self.collection.find_one(sort=[("value", -1)])
        min_jackpot_data = await self.collection.find_one(sort=[("value", 1)])
        
        max_jackpot = None
        min_jackpot = None
        
        if max_jackpot_data:
            max_jackpot = {
                "id": str(max_jackpot_data["_id"]),
                "value": max_jackpot_data["value"],
                "user_id": max_jackpot_data["user_id"],
                "session_id": max_jackpot_data["session_id"],
                "winner_hand": max_jackpot_data.get("winner_hand")
            }
        
        if min_jackpot_data:
            min_jackpot = {
                "id": str(min_jackpot_data["_id"]),
                "value": min_jackpot_data["value"],
                "user_id": min_jackpot_data["user_id"],
                "session_id": min_jackpot_data["session_id"],
                "winner_hand": min_jackpot_data.get("winner_hand")
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
        jackpots_by_user = {stat["_id"]: {"count": stat["count"], "total_value": stat["total_value"]} 
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
        jackpots_by_session = {stat["_id"]: {"count": stat["count"], "total_value": stat["total_value"]} 
                              for stat in session_stats}
        
        # Manos ganadoras más comunes
        hand_pipeline = [
            {"$match": {"winner_hand": {"$ne": None, "$exists": True}}},
            {
                "$group": {
                    "_id": "$winner_hand",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        hand_stats = await self.collection.aggregate(hand_pipeline).to_list(10)
        most_common_hands = {stat["_id"]: stat["count"] for stat in hand_stats}
        
        return {
            "total_jackpots": total_jackpots,
            "total_value": stats["total_value"],
            "average_value": round(stats["average_value"], 2),
            "max_jackpot": max_jackpot,
            "min_jackpot": min_jackpot,
            "high_value_count": high_value_count,
            "jackpots_by_user": jackpots_by_user,
            "jackpots_by_session": jackpots_by_session,
            "most_common_hands": most_common_hands
        }
    
    async def get_user_total_jackpots(self, user_id: str) -> int:
        """
        Obtener el total de jackpots de un usuario.
        """
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": None, "total": {"$sum": "$value"}}}
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(1)
        return result[0]["total"] if result else 0
    
    async def get_session_total_jackpots(self, session_id: str) -> int:
        """
        Obtener el total de jackpots de una sesión.
        """
        pipeline = [
            {"$match": {"session_id": session_id}},
            {"$group": {"_id": None, "total": {"$sum": "$value"}}}
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(1)
        return result[0]["total"] if result else 0
    
    async def get_biggest_jackpot(self) -> Optional[JackpotPriceDomain]:
        """
        Obtener el jackpot más grande.
        """
        jackpot_data = await self.collection.find_one(sort=[("value", -1)])
        
        if jackpot_data:
            jackpot_data["id"] = str(jackpot_data["_id"])
            del jackpot_data["_id"]
            return JackpotPriceDomain(**jackpot_data)
        
        return None

