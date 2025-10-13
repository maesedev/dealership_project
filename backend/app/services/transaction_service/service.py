"""
Servicio Transaction - Orquestador de lógica de transacciones.
Este servicio consume el dominio Transaction pero no lo modifica.
Se encarga de la comunicación con la base de datos y orquestación de operaciones.
"""

from typing import List, Optional
from datetime import datetime
from app.domains.transaction.domain import (
    TransactionDomain, 
    TransactionDomainService,
    OperationType,
    TransactionMedia
)
from app.infrastructure.database.connection import get_database


class TransactionService:
    """
    Servicio de aplicación para Transaction.
    Consume el dominio Transaction y maneja la persistencia.
    """
    
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.transactions
        self.domain_service = TransactionDomainService()
    
    async def create_transaction(self, user_id: str, session_id: str, cantidad: int,
                                operation_type: OperationType, transaction_media: TransactionMedia,
                                comment: str = None) -> TransactionDomain:
        """
        Crear una nueva transacción usando el dominio.
        """
        # Usar el servicio de dominio para crear la transacción
        transaction = self.domain_service.create_transaction(
            user_id=user_id,
            session_id=session_id,
            cantidad=cantidad,
            operation_type=operation_type,
            transaction_media=transaction_media,
            comment=comment
        )
        
        # Convertir a diccionario para MongoDB
        transaction_dict = transaction.dict(exclude={"id"})
        transaction_dict["created_at"] = transaction.created_at
        transaction_dict["updated_at"] = transaction.updated_at
        
        # Insertar en la base de datos
        result = await self.collection.insert_one(transaction_dict)
        
        # Actualizar el ID generado
        transaction.id = str(result.inserted_id)
        
        return transaction
    
    async def create_income(self, user_id: str, session_id: str, cantidad: int,
                           transaction_media: TransactionMedia, 
                           comment: str = None) -> TransactionDomain:
        """
        Crear una transacción de ingreso.
        """
        return await self.create_transaction(
            user_id=user_id,
            session_id=session_id,
            cantidad=cantidad,
            operation_type=OperationType.IN,
            transaction_media=transaction_media,
            comment=comment
        )
    
    async def create_expense(self, user_id: str, session_id: str, cantidad: int,
                            transaction_media: TransactionMedia,
                            comment: str = None) -> TransactionDomain:
        """
        Crear una transacción de egreso.
        """
        return await self.create_transaction(
            user_id=user_id,
            session_id=session_id,
            cantidad=cantidad,
            operation_type=OperationType.OUT,
            transaction_media=transaction_media,
            comment=comment
        )
    
    async def get_transaction_by_id(self, transaction_id: str) -> Optional[TransactionDomain]:
        """
        Obtener una transacción por ID.
        """
        transaction_data = await self.collection.find_one({"_id": transaction_id})
        
        if transaction_data:
            transaction_data["id"] = str(transaction_data["_id"])
            del transaction_data["_id"]
            return TransactionDomain(**transaction_data)
        
        return None
    
    async def get_all_transactions(self, skip: int = 0, limit: int = 100) -> List[TransactionDomain]:
        """
        Obtener todas las transacciones con paginación.
        """
        cursor = self.collection.find().skip(skip).limit(limit).sort("created_at", -1)
        transactions = []
        
        async for transaction_data in cursor:
            transaction_data["id"] = str(transaction_data["_id"])
            del transaction_data["_id"]
            transactions.append(TransactionDomain(**transaction_data))
        
        return transactions
    
    async def get_transactions_by_user(self, user_id: str, skip: int = 0,
                                      limit: int = 100) -> List[TransactionDomain]:
        """
        Obtener transacciones por usuario específico.
        """
        cursor = self.collection.find({"user_id": user_id}).skip(skip).limit(limit).sort("created_at", -1)
        transactions = []
        
        async for transaction_data in cursor:
            transaction_data["id"] = str(transaction_data["_id"])
            del transaction_data["_id"]
            transactions.append(TransactionDomain(**transaction_data))
        
        return transactions
    
    async def get_transactions_by_session(self, session_id: str, skip: int = 0,
                                         limit: int = 100) -> List[TransactionDomain]:
        """
        Obtener transacciones por sesión específica.
        """
        cursor = self.collection.find({"session_id": session_id}).skip(skip).limit(limit).sort("created_at", -1)
        transactions = []
        
        async for transaction_data in cursor:
            transaction_data["id"] = str(transaction_data["_id"])
            del transaction_data["_id"]
            transactions.append(TransactionDomain(**transaction_data))
        
        return transactions
    
    async def get_transactions_by_type(self, operation_type: OperationType,
                                      skip: int = 0, limit: int = 100) -> List[TransactionDomain]:
        """
        Obtener transacciones por tipo de operación.
        """
        cursor = self.collection.find({"operation_type": operation_type.value}).skip(skip).limit(limit).sort("created_at", -1)
        transactions = []
        
        async for transaction_data in cursor:
            transaction_data["id"] = str(transaction_data["_id"])
            del transaction_data["_id"]
            transactions.append(TransactionDomain(**transaction_data))
        
        return transactions
    
    async def get_transactions_by_media(self, transaction_media: TransactionMedia,
                                       skip: int = 0, limit: int = 100) -> List[TransactionDomain]:
        """
        Obtener transacciones por medio de pago.
        """
        cursor = self.collection.find({"transaction_media": transaction_media.value}).skip(skip).limit(limit).sort("created_at", -1)
        transactions = []
        
        async for transaction_data in cursor:
            transaction_data["id"] = str(transaction_data["_id"])
            del transaction_data["_id"]
            transactions.append(TransactionDomain(**transaction_data))
        
        return transactions
    
    async def filter_transactions(self, user_id: str = None, session_id: str = None,
                                 operation_type: OperationType = None,
                                 transaction_media: TransactionMedia = None,
                                 date_from: datetime = None, date_to: datetime = None,
                                 skip: int = 0, limit: int = 100) -> List[TransactionDomain]:
        """
        Filtrar transacciones con múltiples criterios.
        """
        filters = {}
        
        if user_id:
            filters["user_id"] = user_id
        if session_id:
            filters["session_id"] = session_id
        if operation_type:
            filters["operation_type"] = operation_type.value
        if transaction_media:
            filters["transaction_media"] = transaction_media.value
        if date_from or date_to:
            filters["created_at"] = {}
            if date_from:
                filters["created_at"]["$gte"] = date_from
            if date_to:
                filters["created_at"]["$lte"] = date_to
        
        cursor = self.collection.find(filters).skip(skip).limit(limit).sort("created_at", -1)
        transactions = []
        
        async for transaction_data in cursor:
            transaction_data["id"] = str(transaction_data["_id"])
            del transaction_data["_id"]
            transactions.append(TransactionDomain(**transaction_data))
        
        return transactions
    
    async def update_transaction(self, transaction_id: str, **updates) -> Optional[TransactionDomain]:
        """
        Actualizar una transacción existente.
        """
        # Obtener la transacción actual
        existing_transaction = await self.get_transaction_by_id(transaction_id)
        
        if not existing_transaction:
            return None
        
        # Actualizar campos
        for key, value in updates.items():
            if value is not None and hasattr(existing_transaction, key):
                setattr(existing_transaction, key, value)
        
        existing_transaction.updated_at = datetime.utcnow()
        
        # Validar reglas de negocio
        errors = existing_transaction.validate_business_rules()
        if errors:
            raise ValueError(f"Errores de validación: {'; '.join(errors)}")
        
        # Convertir a diccionario para actualización
        update_data = existing_transaction.dict(exclude={"id", "created_at"})
        
        # Actualizar en la base de datos
        await self.collection.update_one(
            {"_id": transaction_id},
            {"$set": update_data}
        )
        
        return existing_transaction
    
    async def delete_transaction(self, transaction_id: str) -> bool:
        """
        Eliminar una transacción.
        """
        result = await self.collection.delete_one({"_id": transaction_id})
        return result.deleted_count > 0
    
    async def get_transaction_stats(self) -> dict:
        """
        Obtener estadísticas de transacciones.
        """
        total_transactions = await self.collection.count_documents({})
        
        # Calcular totales por tipo de operación
        income_pipeline = [
            {"$match": {"operation_type": OperationType.IN.value}},
            {"$group": {"_id": None, "total": {"$sum": "$cantidad"}}}
        ]
        expense_pipeline = [
            {"$match": {"operation_type": OperationType.OUT.value}},
            {"$group": {"_id": None, "total": {"$sum": "$cantidad"}}}
        ]
        
        income_result = await self.collection.aggregate(income_pipeline).to_list(1)
        expense_result = await self.collection.aggregate(expense_pipeline).to_list(1)
        
        total_income = income_result[0]["total"] if income_result else 0
        total_expenses = expense_result[0]["total"] if expense_result else 0
        net_balance = total_income - total_expenses
        
        # Contar por medio de transacción
        digital_count = await self.collection.count_documents({"transaction_media": TransactionMedia.DIGITAL.value})
        cash_count = await self.collection.count_documents({"transaction_media": TransactionMedia.CASH.value})
        
        # Totales por tipo y medio
        income_by_media = {}
        expenses_by_media = {}
        
        for media in TransactionMedia:
            income_media = await self.collection.aggregate([
                {"$match": {"operation_type": OperationType.IN.value, "transaction_media": media.value}},
                {"$group": {"_id": None, "total": {"$sum": "$cantidad"}}}
            ]).to_list(1)
            
            expenses_media = await self.collection.aggregate([
                {"$match": {"operation_type": OperationType.OUT.value, "transaction_media": media.value}},
                {"$group": {"_id": None, "total": {"$sum": "$cantidad"}}}
            ]).to_list(1)
            
            income_by_media[media.value] = income_media[0]["total"] if income_media else 0
            expenses_by_media[media.value] = expenses_media[0]["total"] if expenses_media else 0
        
        return {
            "total_transactions": total_transactions,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_balance": net_balance,
            "digital_transactions": digital_count,
            "cash_transactions": cash_count,
            "income_by_media": income_by_media,
            "expenses_by_media": expenses_by_media
        }
    
    async def get_session_balance(self, session_id: str) -> dict:
        """
        Obtener balance de transacciones para una sesión específica.
        """
        # Ingresos de la sesión
        income_result = await self.collection.aggregate([
            {"$match": {"session_id": session_id, "operation_type": OperationType.IN.value}},
            {"$group": {"_id": None, "total": {"$sum": "$cantidad"}}}
        ]).to_list(1)
        
        # Egresos de la sesión
        expense_result = await self.collection.aggregate([
            {"$match": {"session_id": session_id, "operation_type": OperationType.OUT.value}},
            {"$group": {"_id": None, "total": {"$sum": "$cantidad"}}}
        ]).to_list(1)
        
        total_income = income_result[0]["total"] if income_result else 0
        total_expenses = expense_result[0]["total"] if expense_result else 0
        
        return {
            "session_id": session_id,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_balance": total_income - total_expenses
        }

