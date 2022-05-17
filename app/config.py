import os


class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///la_poste_nicpoyia.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    ENV_TYPE = "development"
    LA_POSTE_API_BASE_URL = "https://api.laposte.fr/ssu/v1"
    LA_POSTE_API_KEY = os.environ.get('LA_POSTE_API_KEY')
    APP_DEBUG = True


class ProductionConfig(Config):
    ENV_TYPE = "production"
    LA_POSTE_API_BASE_URL = "https://api.laposte.fr/ssu/v1"
    LA_POSTE_API_KEY = os.environ.get('LA_POSTE_API_KEY')


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
