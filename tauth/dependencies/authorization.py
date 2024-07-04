from ..authz.engines.factory import AuthorizationEngine


def init_app():
    authz_engine = AuthorizationEngine.get()
