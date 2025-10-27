"""
Configuración de conexión a MongoDB.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from app.core.config import settings
from app.shared.utils.logger import get_logger

# Logger para este módulo
logger = get_logger(__name__)


class Database:
    """Cliente de base de datos MongoDB"""
    client: AsyncIOMotorClient = None
    database = None


# Instancia global de la base de datos
db = Database()


async def connect_to_mongo():
    """Conectar a MongoDB con ServerApi"""
    try:
        # Crear cliente con ServerApi para MongoDB Atlas
        db.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            server_api=ServerApi('1')
        )
        db.database = db.client[settings.MONGODB_DATABASE]
        
        # Enviar un ping para confirmar una conexión exitosa
        await db.client.admin.command('ping')
        logger.info("✅ Pinged your deployment. You successfully connected to MongoDB!")
        logger.info(f"✅ Conectado a la base de datos: {settings.MONGODB_DATABASE}")
    except Exception as e:
        logger.error(f"❌ Error al conectar a MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Cerrar conexión a MongoDB"""
    if db.client:
        db.client.close()
        logger.info("❌ Conexión a MongoDB cerrada")


def get_database():
    """Obtener instancia de la base de datos"""
    return db.database
