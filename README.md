# TAuth

FastAPI-compatible authentication "middleware" for Teia Web Services.
Pronounced tee-auth.

## Usage

To use a tauth API key in your FastAPI app:

```python
from tauth.dependencies import security
app = FastAPI()
security.init_app(app)
```

To host the clients and clients/tokens CRUD in your app:

```python
from tauth.routes import get_router
app = FastAPI()
app.include_router(get_router(prefix=None))
```
