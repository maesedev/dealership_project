"""
Servicio DailyReport - Orquestador de lógica de reportes diarios.
Este servicio consume el dominio DailyReport pero no lo modifica.
Se encarga de la comunicación con la base de datos y orquestación de operaciones.
"""

from typing import List, Optional
from datetime import datetime, date
from app.domains.daily_report.domain import DailyReportDomain, DailyReportDomainService
from app.infrastructure.database.connection import get_database


class DailyReportService:
    """
    Servicio de aplicación para DailyReport.
    Consume el dominio DailyReport y maneja la persistencia.
    """
    
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.daily_reports
        self.domain_service = DailyReportDomainService()
    
    async def create_daily_report(self, report_date: date, reik: int = 0, 
                                 jackpot: int = 0, ganancias: int = 0,
                                 gastos: int = 0, sessions: List[str] = None, 
                                 comment: str = None) -> DailyReportDomain:
        """
        Crear un nuevo reporte diario usando el dominio.
        """
        # Verificar que no exista ya un reporte para esa fecha
        existing_report = await self.get_report_by_date(report_date)
        if existing_report:
            raise ValueError(f"Ya existe un reporte para la fecha {report_date}")
        
        # Usar el servicio de dominio para crear el reporte
        daily_report = self.domain_service.create_daily_report(
            report_date=report_date,
            reik=reik,
            jackpot=jackpot,
            ganancias=ganancias,
            gastos=gastos,
            sessions=sessions,
            comment=comment
        )
        
        # Convertir a diccionario para MongoDB
        report_dict = daily_report.dict(exclude={"id"})
        report_dict["created_at"] = daily_report.created_at
        report_dict["updated_at"] = daily_report.updated_at
        
        # Insertar en la base de datos
        result = await self.collection.insert_one(report_dict)
        
        # Actualizar el ID generado
        daily_report.id = str(result.inserted_id)
        
        return daily_report
    
    async def get_report_by_id(self, report_id: str) -> Optional[DailyReportDomain]:
        """
        Obtener un reporte por ID.
        """
        report_data = await self.collection.find_one({"_id": report_id})
        
        if report_data:
            report_data["id"] = str(report_data["_id"])
            del report_data["_id"]
            return DailyReportDomain(**report_data)
        
        return None
    
    async def get_report_by_date(self, report_date: date) -> Optional[DailyReportDomain]:
        """
        Obtener un reporte por fecha.
        """
        report_data = await self.collection.find_one({"date": report_date})
        
        if report_data:
            report_data["id"] = str(report_data["_id"])
            del report_data["_id"]
            return DailyReportDomain(**report_data)
        
        return None
    
    async def get_all_reports(self, skip: int = 0, limit: int = 100) -> List[DailyReportDomain]:
        """
        Obtener todos los reportes con paginación.
        """
        cursor = self.collection.find().skip(skip).limit(limit).sort("date", -1)
        reports = []
        
        async for report_data in cursor:
            report_data["id"] = str(report_data["_id"])
            del report_data["_id"]
            reports.append(DailyReportDomain(**report_data))
        
        return reports
    
    async def get_reports_by_date_range(self, date_from: date, date_to: date,
                                       skip: int = 0, limit: int = 100) -> List[DailyReportDomain]:
        """
        Obtener reportes en un rango de fechas.
        """
        cursor = self.collection.find({
            "date": {"$gte": date_from, "$lte": date_to}
        }).skip(skip).limit(limit).sort("date", -1)
        reports = []
        
        async for report_data in cursor:
            report_data["id"] = str(report_data["_id"])
            del report_data["_id"]
            reports.append(DailyReportDomain(**report_data))
        
        return reports
    
    async def get_profitable_reports(self, skip: int = 0, limit: int = 100) -> List[DailyReportDomain]:
        """
        Obtener reportes con ganancia positiva.
        """
        cursor = self.collection.find().skip(skip).limit(limit).sort("date", -1)
        reports = []
        
        async for report_data in cursor:
            report_data["id"] = str(report_data["_id"])
            del report_data["_id"]
            report = DailyReportDomain(**report_data)
            if report.is_profitable():
                reports.append(report)
        
        return reports
    
    async def update_report(self, report_id: str, **updates) -> Optional[DailyReportDomain]:
        """
        Actualizar un reporte existente.
        """
        # Obtener el reporte actual
        existing_report = await self.get_report_by_id(report_id)
        
        if not existing_report:
            return None
        
        # Actualizar campos
        for key, value in updates.items():
            if value is not None and hasattr(existing_report, key):
                setattr(existing_report, key, value)
        
        existing_report.updated_at = datetime.utcnow()
        
        # Validar reglas de negocio
        errors = existing_report.validate_business_rules()
        if errors:
            raise ValueError(f"Errores de validación: {'; '.join(errors)}")
        
        # Convertir a diccionario para actualización
        update_data = existing_report.dict(exclude={"id", "created_at"})
        
        # Actualizar en la base de datos
        await self.collection.update_one(
            {"_id": report_id},
            {"$set": update_data}
        )
        
        return existing_report
    
    async def add_income(self, report_id: str, amount: int, income_type: str) -> Optional[DailyReportDomain]:
        """
        Agregar ingresos a un reporte.
        """
        existing_report = await self.get_report_by_id(report_id)
        
        if not existing_report:
            return None
        
        updated_report = self.domain_service.add_income(existing_report, amount, income_type)
        
        await self.collection.update_one(
            {"_id": report_id},
            {"$set": {
                "reik": updated_report.reik,
                "jackpot": updated_report.jackpot,
                "ganancias": updated_report.ganancias,
                "updated_at": updated_report.updated_at
            }}
        )
        
        return updated_report
    
    async def add_expense(self, report_id: str, amount: int) -> Optional[DailyReportDomain]:
        """
        Agregar gastos a un reporte.
        """
        existing_report = await self.get_report_by_id(report_id)
        
        if not existing_report:
            return None
        
        updated_report = self.domain_service.add_expense(existing_report, amount)
        
        await self.collection.update_one(
            {"_id": report_id},
            {"$set": {
                "gastos": updated_report.gastos,
                "updated_at": updated_report.updated_at
            }}
        )
        
        return updated_report
    
    async def delete_report(self, report_id: str) -> bool:
        """
        Eliminar un reporte.
        """
        result = await self.collection.delete_one({"_id": report_id})
        return result.deleted_count > 0
    
    async def get_report_stats(self, date_from: date = None, date_to: date = None) -> dict:
        """
        Obtener estadísticas de reportes.
        """
        # Construir filtro de fecha
        date_filter = {}
        if date_from or date_to:
            date_filter["date"] = {}
            if date_from:
                date_filter["date"]["$gte"] = date_from
            if date_to:
                date_filter["date"]["$lte"] = date_to
        
        # Contar reportes
        total_reports = await self.collection.count_documents(date_filter)
        
        # Calcular totales
        pipeline = [
            {"$match": date_filter} if date_filter else {"$match": {}},
            {
                "$group": {
                    "_id": None,
                    "total_reik": {"$sum": "$reik"},
                    "total_jackpot": {"$sum": "$jackpot"},
                    "total_ganancias": {"$sum": "$ganancias"},
                    "total_gastos": {"$sum": "$gastos"}
                }
            }
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(1)
        totals = result[0] if result else {
            "total_reik": 0,
            "total_jackpot": 0,
            "total_ganancias": 0,
            "total_gastos": 0
        }
        
        total_net_profit = (
            totals["total_reik"] + 
            totals["total_jackpot"] + 
            totals["total_ganancias"] - 
            totals["total_gastos"]
        )
        
        average_daily_profit = total_net_profit / total_reports if total_reports > 0 else 0
        
        # Contar días rentables y no rentables
        cursor = self.collection.find(date_filter)
        profitable_days = 0
        unprofitable_days = 0
        best_day = None
        worst_day = None
        best_profit = float('-inf')
        worst_profit = float('inf')
        
        async for report_data in cursor:
            report_data["id"] = str(report_data["_id"])
            del report_data["_id"]
            report = DailyReportDomain(**report_data)
            
            net_profit = report.get_net_profit()
            
            if report.is_profitable():
                profitable_days += 1
            else:
                unprofitable_days += 1
            
            if net_profit > best_profit:
                best_profit = net_profit
                best_day = {
                    "date": report.date.isoformat(),
                    "net_profit": net_profit
                }
            
            if net_profit < worst_profit:
                worst_profit = net_profit
                worst_day = {
                    "date": report.date.isoformat(),
                    "net_profit": net_profit
                }
        
        return {
            "total_reports": total_reports,
            "total_reik": totals["total_reik"],
            "total_jackpot": totals["total_jackpot"],
            "total_ganancias": totals["total_ganancias"],
            "total_gastos": totals["total_gastos"],
            "total_net_profit": total_net_profit,
            "average_daily_profit": round(average_daily_profit, 2),
            "profitable_days": profitable_days,
            "unprofitable_days": unprofitable_days,
            "best_day": best_day,
            "worst_day": worst_day
        }

