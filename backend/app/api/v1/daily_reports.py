"""
Endpoints para la gestión de reportes diarios.
"""

from typing import List
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import APIRouter, HTTPException, Depends, status
from app.services.daily_report_service.service import DailyReportService
from app.services.session_service.service import SessionService
from app.shared.schemas.daily_report_schemas import (
    DailyReportCreateSchema,
    DailyReportUpdateSchema,
    DailyReportResponseSchema,
    DailyReportListResponseSchema,
    DailyReportStatsSchema
)
from app.domains.user.domain import UserDomain
from app.shared.dependencies.auth import (
    get_current_manager_or_admin
)
from app.shared.dependencies.services import (
    get_daily_report_service,
    get_session_service
)

# Zona horaria de Bogotá
BOGOTA_TZ = ZoneInfo("America/Bogota")

# Crear router para daily reports
router = APIRouter()


async def generate_daily_report_from_sessions(
    report_date: date, 
    session_service: SessionService,
    daily_report_service: DailyReportService
):
    """
    Genera un reporte diario a partir de las sesiones del día.
    
    El reporte suma:
    - reik de todas las sesiones
    - jackpot de todas las sesiones
    - costo del dealer (duración de sesión × hourly_pay)
    """
    # Obtener todas las sesiones del día
    start_of_day = datetime.combine(report_date, datetime.min.time())
    end_of_day = datetime.combine(report_date, datetime.max.time())
    
    sessions = await session_service.get_sessions_by_date_range(start_of_day, end_of_day)
    
    # Inicializar valores
    total_reik = 0
    total_jackpot = 0
    total_gastos = 0
    session_ids = []
    
    # Sumar valores de cada sesión
    for session in sessions:
        total_reik += session.reik
        total_jackpot += session.jackpot
        session_ids.append(session.id)
        
        # Calcular costo del dealer (duración × hourly_pay)
        if session.start_time and session.hourly_pay:
            # Si la sesión tiene end_time, calcular duración exacta
            if session.end_time:
                duration_hours = (session.end_time - session.start_time).total_seconds() / 3600
            else:
                # Si no tiene end_time, asumir que sigue activa hasta ahora
                duration_hours = (datetime.now(timezone.utc) - session.start_time).total_seconds() / 3600
            
            dealer_cost = duration_hours * session.hourly_pay
            total_gastos += int(dealer_cost)
    
    # Ganancias = reik + jackpot (puede ajustarse según lógica de negocio)
    total_ganancias = total_reik + total_jackpot
    
    # Crear el reporte
    report = await daily_report_service.create_daily_report(
        report_date=report_date,
        reik=total_reik,
        jackpot=total_jackpot,
        ganancias=total_ganancias,
        gastos=total_gastos,
        sessions=session_ids,
        comment=f"Reporte generado automáticamente con {len(sessions)} sesiones"
    )
    
    return report


@router.get("/date/{report_date}", response_model=DailyReportResponseSchema)
async def get_daily_report_by_date(
    report_date: date,
    current_user: UserDomain = Depends(get_current_manager_or_admin),
    daily_report_service: DailyReportService = Depends(get_daily_report_service),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Obtener reporte diario por fecha.
    
    Permisos:
    - Solo Managers y Admins pueden consultar reportes diarios
    
    Comportamiento:
    - Si la fecha es HOY (Bogotá): SIEMPRE regenera el reporte (datos en tiempo real)
    - Si la fecha es pasada: Devuelve existente o genera si no existe
    """
    try:
        # Obtener fecha actual en Bogotá
        now_bogota = datetime.now(BOGOTA_TZ)
        today_bogota = now_bogota.date()
        
        # Verificar si la fecha solicitada es HOY
        is_today = report_date == today_bogota
        
        if is_today:
            # Si es HOY, SIEMPRE regenerar el reporte
            # Primero eliminar el reporte existente si hay uno
            existing_report = await daily_report_service.get_report_by_date(report_date)
            if existing_report:
                await daily_report_service.delete_report(existing_report.id)
            
            # Generar nuevo reporte con datos actuales
            report = await generate_daily_report_from_sessions(report_date, session_service, daily_report_service)
        else:
            # Si es fecha pasada, usar comportamiento normal
            # Intentar obtener el reporte existente
            report = await daily_report_service.get_report_by_date(report_date)
            
            # Si no existe, generarlo automáticamente
            if not report:
                report = await generate_daily_report_from_sessions(report_date, session_service, daily_report_service)
        
        return DailyReportResponseSchema(
            id=report.id,
            date=report.date,
            reik=report.reik,
            jackpot=report.jackpot,
            ganancias=report.ganancias,
            gastos=report.gastos,
            sessions=report.sessions,
            comment=report.comment,
            created_at=report.created_at,
            updated_at=report.updated_at,
            net_profit=report.get_net_profit(),
            total_income=report.get_total_income(),
            is_profitable=report.is_profitable(),
            profit_margin=report.get_profit_margin()
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{report_id}", response_model=DailyReportResponseSchema)
async def get_daily_report(
    report_id: str,
    current_user: UserDomain = Depends(get_current_manager_or_admin),
    daily_report_service: DailyReportService = Depends(get_daily_report_service)
):
    """
    Obtener un reporte diario por ID.
    Solo Managers y Admins pueden consultar reportes.
    """
    report = await daily_report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporte diario no encontrado"
        )
    
    return DailyReportResponseSchema(
        id=report.id,
        date=report.date,
        reik=report.reik,
        jackpot=report.jackpot,
        ganancias=report.ganancias,
        gastos=report.gastos,
        sessions=report.sessions,
        comment=report.comment,
        created_at=report.created_at,
        updated_at=report.updated_at,
        net_profit=report.get_net_profit(),
        total_income=report.get_total_income(),
        is_profitable=report.is_profitable(),
        profit_margin=report.get_profit_margin()
    )


@router.get("/", response_model=DailyReportListResponseSchema)
async def get_daily_reports(
    skip: int = 0,
    limit: int = 100,
    date_from: date = None,
    date_to: date = None,
    current_user: UserDomain = Depends(get_current_manager_or_admin),
    daily_report_service: DailyReportService = Depends(get_daily_report_service)
):
    """
    Obtener lista de reportes diarios con paginación.
    Opcionalmente filtrar por rango de fechas.
    Solo Managers y Admins pueden consultar reportes.
    """
    if date_from and date_to:
        reports = await daily_report_service.get_reports_by_date_range(
            date_from, date_to, skip=skip, limit=limit
        )
    else:
        reports = await daily_report_service.get_all_reports(skip=skip, limit=limit)
    
    total = len(reports)
    report_responses = [
        DailyReportResponseSchema(
            id=r.id,
            date=r.date,
            reik=r.reik,
            jackpot=r.jackpot,
            ganancias=r.ganancias,
            gastos=r.gastos,
            sessions=r.sessions,
            comment=r.comment,
            created_at=r.created_at,
            updated_at=r.updated_at,
            net_profit=r.get_net_profit(),
            total_income=r.get_total_income(),
            is_profitable=r.is_profitable(),
            profit_margin=r.get_profit_margin()
        )
        for r in reports
    ]
    
    return DailyReportListResponseSchema(
        reports=report_responses,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        limit=limit
    )


@router.get("/profitable/list", response_model=DailyReportListResponseSchema)
async def get_profitable_reports(
    skip: int = 0,
    limit: int = 100,
    current_user: UserDomain = Depends(get_current_manager_or_admin),
    daily_report_service: DailyReportService = Depends(get_daily_report_service)
):
    """
    Obtener lista de reportes diarios con ganancia positiva.
    Solo Managers y Admins pueden consultar reportes.
    """
    reports = await daily_report_service.get_profitable_reports(skip=skip, limit=limit)
    total = len(reports)
    report_responses = [
        DailyReportResponseSchema(
            id=r.id,
            date=r.date,
            reik=r.reik,
            jackpot=r.jackpot,
            ganancias=r.ganancias,
            gastos=r.gastos,
            sessions=r.sessions,
            comment=r.comment,
            created_at=r.created_at,
            updated_at=r.updated_at,
            net_profit=r.get_net_profit(),
            total_income=r.get_total_income(),
            is_profitable=r.is_profitable(),
            profit_margin=r.get_profit_margin()
        )
        for r in reports
    ]
    
    return DailyReportListResponseSchema(
        reports=report_responses,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        limit=limit
    )


@router.post("/", response_model=DailyReportResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_daily_report(
    report_data: DailyReportCreateSchema,
    current_user: UserDomain = Depends(get_current_manager_or_admin),
    daily_report_service: DailyReportService = Depends(get_daily_report_service)
):
    """
    Crear un reporte diario manualmente.
    Solo Managers y Admins pueden crear reportes.
    """
    try:
        report = await daily_report_service.create_daily_report(
            report_date=report_data.date,
            reik=report_data.reik,
            jackpot=report_data.jackpot,
            ganancias=report_data.ganancias,
            gastos=report_data.gastos,
            sessions=report_data.sessions,
            comment=report_data.comment
        )
        
        return DailyReportResponseSchema(
            id=report.id,
            date=report.date,
            reik=report.reik,
            jackpot=report.jackpot,
            ganancias=report.ganancias,
            gastos=report.gastos,
            sessions=report.sessions,
            comment=report.comment,
            created_at=report.created_at,
            updated_at=report.updated_at,
            net_profit=report.get_net_profit(),
            total_income=report.get_total_income(),
            is_profitable=report.is_profitable(),
            profit_margin=report.get_profit_margin()
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{report_id}", response_model=DailyReportResponseSchema)
async def update_daily_report(
    report_id: str,
    report_data: DailyReportUpdateSchema,
    current_user: UserDomain = Depends(get_current_manager_or_admin),
    daily_report_service: DailyReportService = Depends(get_daily_report_service)
):
    """
    Actualizar un reporte diario.
    Solo Managers y Admins pueden actualizar reportes.
    """
    try:
        # Construir diccionario de actualizaciones
        update_dict = {}
        if report_data.reik is not None:
            update_dict["reik"] = report_data.reik
        if report_data.jackpot is not None:
            update_dict["jackpot"] = report_data.jackpot
        if report_data.ganancias is not None:
            update_dict["ganancias"] = report_data.ganancias
        if report_data.gastos is not None:
            update_dict["gastos"] = report_data.gastos
        if report_data.sessions is not None:
            update_dict["sessions"] = report_data.sessions
        if report_data.comment is not None:
            update_dict["comment"] = report_data.comment
        
        report = await daily_report_service.update_report(report_id, **update_dict)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporte diario no encontrado"
            )
        
        return DailyReportResponseSchema(
            id=report.id,
            date=report.date,
            reik=report.reik,
            jackpot=report.jackpot,
            ganancias=report.ganancias,
            gastos=report.gastos,
            sessions=report.sessions,
            comment=report.comment,
            created_at=report.created_at,
            updated_at=report.updated_at,
            net_profit=report.get_net_profit(),
            total_income=report.get_total_income(),
            is_profitable=report.is_profitable(),
            profit_margin=report.get_profit_margin()
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/stats/overview", response_model=DailyReportStatsSchema)
async def get_daily_report_stats(
    date_from: date = None,
    date_to: date = None,
    current_user: UserDomain = Depends(get_current_manager_or_admin),
    daily_report_service: DailyReportService = Depends(get_daily_report_service)
):
    """
    Obtener estadísticas de reportes diarios.
    Opcionalmente filtrar por rango de fechas.
    Solo Managers y Admins pueden ver estadísticas.
    """
    stats = await daily_report_service.get_report_stats(date_from=date_from, date_to=date_to)
    return DailyReportStatsSchema(**stats)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_daily_report(
    report_id: str,
    current_user: UserDomain = Depends(get_current_manager_or_admin),
    daily_report_service: DailyReportService = Depends(get_daily_report_service)
):
    """
    Eliminar un reporte diario.
    Solo Managers y Admins pueden eliminar reportes.
    """
    success = await daily_report_service.delete_report(report_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporte diario no encontrado"
        )
    
    return None



