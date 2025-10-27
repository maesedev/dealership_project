"""
Servicio Session - Orquestador de lógica de sesiones.
Este servicio consume el dominio Session pero no lo modifica.
Se encarga de la comunicación con la base de datos y orquestación de operaciones.
"""

from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from app.domains.session.domain import SessionDomain, SessionDomainService
from app.infrastructure.database.connection import get_database
from app.shared.utils import now_bogota


class SessionService:
    """
    Servicio de aplicación para Session.
    Consume el dominio Session y maneja la persistencia.
    """
    
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.sessions
        self.domain_service = SessionDomainService()
    
    async def create_session(self, dealer_id: str, start_time: datetime = None,
                            end_time: datetime = None, jackpot: int = 0, reik: int = 0,
                            tips: int = 0, hourly_pay: int = 0, comment: str = None) -> SessionDomain:
        """
        Crear una nueva sesión usando el dominio.
        
        Regla de negocio:
        - Un usuario solo puede tener una sesión abierta a la vez
        """
        # Verificar si el dealer ya tiene una sesión activa
        active_session = await self.get_active_session_by_dealer(dealer_id)
        if active_session:
            raise ValueError(
                f"El usuario ya tiene una sesión activa (ID: {active_session.id}). "
                "Debe cerrar la sesión actual antes de abrir una nueva."
            )
        
        # Usar el servicio de dominio para crear la sesión
        session = self.domain_service.create_session(
            dealer_id=dealer_id,
            start_time=start_time,
            hourly_pay=hourly_pay,
            comment=comment
        )
        
        # Establecer valores adicionales
        if end_time:
            session.end_time = end_time
        session.jackpot = jackpot
        session.reik = reik
        session.tips = tips
        
        # Convertir a diccionario para MongoDB
        session_dict = session.dict(exclude={"id"})
        session_dict["created_at"] = session.created_at
        session_dict["updated_at"] = session.updated_at
        
        # Insertar en la base de datos
        result = await self.collection.insert_one(session_dict)
        
        # Actualizar el ID generado
        session.id = str(result.inserted_id)
        
        return session
    
    async def get_session_by_id(self, session_id: str) -> Optional[SessionDomain]:
        """
        Obtener una sesión por ID.
        """
        session_data = await self.collection.find_one({"_id": ObjectId(session_id)})
        
        if session_data:
            session_data["id"] = str(session_data["_id"])
            del session_data["_id"]
            return SessionDomain(**session_data)
        
        return None
    
    async def get_all_sessions(self, skip: int = 0, limit: int = 100) -> List[SessionDomain]:
        """
        Obtener todas las sesiones con paginación.
        """
        cursor = self.collection.find().skip(skip).limit(limit).sort("start_time", -1)
        sessions = []
        
        async for session_data in cursor:
            session_data["id"] = str(session_data["_id"])
            del session_data["_id"]
            sessions.append(SessionDomain(**session_data))
        
        return sessions
    
    async def get_sessions_by_dealer(self, dealer_id: str, skip: int = 0, 
                                    limit: int = 100) -> List[SessionDomain]:
        """
        Obtener sesiones por dealer específico.
        """
        cursor = self.collection.find({"dealer_id": dealer_id}).skip(skip).limit(limit).sort("start_time", -1)
        sessions = []
        
        async for session_data in cursor:
            session_data["id"] = str(session_data["_id"])
            del session_data["_id"]
            sessions.append(SessionDomain(**session_data))
        
        return sessions
    
    async def get_active_sessions(self, skip: int = 0, limit: int = 100) -> List[SessionDomain]:
        """
        Obtener sesiones activas (sin end_time).
        """
        cursor = self.collection.find({"end_time": None}).skip(skip).limit(limit).sort("start_time", -1)
        sessions = []
        
        async for session_data in cursor:
            session_data["id"] = str(session_data["_id"])
            del session_data["_id"]
            sessions.append(SessionDomain(**session_data))
        
        return sessions
    
    async def get_sessions_by_date_range(self, start_date: datetime, end_date: datetime,
                                        skip: int = 0, limit: int = 100) -> List[SessionDomain]:
        """
        Obtener sesiones en un rango de fechas.
        """
        cursor = self.collection.find({
            "start_time": {"$gte": start_date, "$lte": end_date}
        }).skip(skip).limit(limit).sort("start_time", -1)
        sessions = []
        
        async for session_data in cursor:
            session_data["id"] = str(session_data["_id"])
            del session_data["_id"]
            sessions.append(SessionDomain(**session_data))
        
        return sessions
    
    async def get_active_session_by_dealer(self, dealer_id: str) -> Optional[SessionDomain]:
        """
        Obtener sesión activa de un dealer específico.
        """
        session_data = await self.collection.find_one({
            "dealer_id": dealer_id,
            "end_time": None
        })
        
        if session_data:
            session_data["id"] = str(session_data["_id"])
            del session_data["_id"]
            return SessionDomain(**session_data)
        
        return None
    
    async def get_active_sessions_by_dealer(self, dealer_id: str, skip: int = 0, 
                                           limit: int = 100) -> List[SessionDomain]:
        """
        Obtener todas las sesiones activas de un dealer específico.
        """
        cursor = self.collection.find({
            "dealer_id": dealer_id,
            "end_time": None
        }).skip(skip).limit(limit).sort("start_time", -1)
        sessions = []
        
        async for session_data in cursor:
            session_data["id"] = str(session_data["_id"])
            del session_data["_id"]
            sessions.append(SessionDomain(**session_data))
        
        return sessions
    
    async def update_session(self, session_id: str, **updates) -> Optional[SessionDomain]:
        """
        Actualizar una sesión existente.
        """
        # Obtener la sesión actual
        existing_session = await self.get_session_by_id(session_id)
        
        if not existing_session:
            return None
        
        # Actualizar campos
        for key, value in updates.items():
            if value is not None and hasattr(existing_session, key):
                setattr(existing_session, key, value)
        
        existing_session.updated_at = now_bogota()
        
        # Validar reglas de negocio
        errors = existing_session.validate_business_rules()
        if errors:
            raise ValueError(f"Errores de validación: {'; '.join(errors)}")
        
        # Convertir a diccionario para actualización
        update_data = existing_session.dict(exclude={"id", "created_at"})
        
        # Actualizar en la base de datos
        await self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": update_data}
        )
        
        return existing_session
    
    async def end_session(self, session_id: str, end_time: datetime = None) -> Optional[SessionDomain]:
        """
        Finalizar una sesión.
        """
        existing_session = await self.get_session_by_id(session_id)
        
        if not existing_session:
            return None
        
        # Usar el servicio de dominio para finalizar
        ended_session = self.domain_service.end_session(existing_session, end_time)
        
        await self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {
                "end_time": ended_session.end_time,
                "updated_at": ended_session.updated_at
            }}
        )
        
        return ended_session
    
    async def add_jackpot(self, session_id: str, amount: int) -> Optional[SessionDomain]:
        """
        Agregar monto al jackpot de la sesión.
        """
        existing_session = await self.get_session_by_id(session_id)
        
        if not existing_session:
            return None
        
        updated_session = self.domain_service.add_jackpot(existing_session, amount)
        
        await self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {
                "jackpot": updated_session.jackpot,
                "updated_at": updated_session.updated_at
            }}
        )
        
        return updated_session
    
    async def add_reik(self, session_id: str, amount: int) -> Optional[SessionDomain]:
        """
        Agregar monto al reik de la sesión.
        """
        existing_session = await self.get_session_by_id(session_id)
        
        if not existing_session:
            return None
        
        updated_session = self.domain_service.add_reik(existing_session, amount)
        
        await self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {
                "reik": updated_session.reik,
                "updated_at": updated_session.updated_at
            }}
        )
        
        return updated_session
    
    async def add_tips(self, session_id: str, amount: int) -> Optional[SessionDomain]:
        """
        Agregar propinas a la sesión.
        """
        existing_session = await self.get_session_by_id(session_id)
        
        if not existing_session:
            return None
        
        updated_session = self.domain_service.add_tips(existing_session, amount)
        
        await self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {
                "tips": updated_session.tips,
                "updated_at": updated_session.updated_at
            }}
        )
        
        return updated_session
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Eliminar una sesión.
        """
        result = await self.collection.delete_one({"_id": ObjectId(session_id)})
        return result.deleted_count > 0
    
    async def get_session_stats(self) -> dict:
        """
        Obtener estadísticas de sesiones.
        """
        total_sessions = await self.collection.count_documents({})
        active_sessions = await self.collection.count_documents({"end_time": None})
        completed_sessions = await self.collection.count_documents({"end_time": {"$ne": None}})
        
        # Calcular totales
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_jackpot": {"$sum": "$jackpot"},
                    "total_reik": {"$sum": "$reik"},
                    "total_tips": {"$sum": "$tips"},
                    "total_hourly_pay": {"$sum": "$hourly_pay"}
                }
            }
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(1)
        totals = result[0] if result else {
            "total_jackpot": 0,
            "total_reik": 0,
            "total_tips": 0,
            "total_hourly_pay": 0
        }
        
        total_earnings = (
            totals["total_jackpot"] + 
            totals["total_reik"] + 
            totals["total_tips"] + 
            totals["total_hourly_pay"]
        )
        
        # Calcular duración promedio
        completed_cursor = self.collection.find({"end_time": {"$ne": None}})
        durations = []
        async for session_data in completed_cursor:
            session_data["id"] = str(session_data["_id"])
            del session_data["_id"]
            session = SessionDomain(**session_data)
            duration = session.get_duration()
            if duration:
                durations.append(duration)
        
        average_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "completed_sessions": completed_sessions,
            "total_jackpot": totals["total_jackpot"],
            "total_reik": totals["total_reik"],
            "total_tips": totals["total_tips"],
            "total_earnings": total_earnings,
            "average_duration_hours": round(average_duration, 2)
        }

