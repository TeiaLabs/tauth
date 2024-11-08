import subprocess
import sys
from pathlib import Path

import uvicorn

from .settings import Settings


def main():
    settings = Settings()

    # Authorization API
    # improved debug logging: --log-format=json-pretty
    path_opa_executable = Path(__file__).parents[1] / "opa"
    subprocess.Popen(
        f"{path_opa_executable} run --server --log-level=debug --v1-compatible",
        shell=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    uvicorn.run(
        app="tauth.app:create_app",
        factory=True,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
