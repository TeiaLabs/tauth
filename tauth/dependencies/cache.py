from cacheia_api.settings import Settings as CacheiaSettings
from cacheia_client import configure


def init_app():
    sets = CacheiaSettings()
    configure(url=f"http://{sets.CACHEIA_HOST}:{sets.CACHEIA_PORT}")
