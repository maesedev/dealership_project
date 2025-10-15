"""
Funciones de dependencia para servicios.
Estos servicios se instancian de forma lazy para asegurar que MongoDB esté conectado.
"""

from app.services.user_service.service import UserService
from app.services.session_service.service import SessionService
from app.services.transaction_service.service import TransactionService
from app.services.bono_service.service import BonoService
from app.services.daily_report_service.service import DailyReportService
from app.services.jackpot_price_service.service import JackpotPriceService
from app.services.auth_service.service import AuthService


def get_user_service() -> UserService:
    """Obtener instancia del servicio de usuarios"""
    return UserService()


def get_session_service() -> SessionService:
    """Obtener instancia del servicio de sesiones"""
    return SessionService()


def get_transaction_service() -> TransactionService:
    """Obtener instancia del servicio de transacciones"""
    return TransactionService()


def get_bono_service() -> BonoService:
    """Obtener instancia del servicio de bonos"""
    return BonoService()


def get_daily_report_service() -> DailyReportService:
    """Obtener instancia del servicio de reportes diarios"""
    return DailyReportService()


def get_jackpot_price_service() -> JackpotPriceService:
    """Obtener instancia del servicio de precios de jackpot"""
    return JackpotPriceService()


def get_auth_service() -> AuthService:
    """Obtener instancia del servicio de autenticación"""
    return AuthService()

