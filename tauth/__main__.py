import subprocess
import sys

import uvicorn

from .settings import Settings


def main():
    settings = Settings()

    # Caching API
    subprocess.Popen(
        "python -m cacheia_api",
        shell=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    # Authorization API
    # improved debug logging: --log-format=json-pretty
    subprocess.Popen(
        "./opa run --server --log-level=debug --v1-compatible",
        shell=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    uvicorn.run(
        app="tauth.app:create_app",
        factory=True,
        forwarded_allow_ips="*",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS,
    )


if __name__ == "__main__":
    main()
