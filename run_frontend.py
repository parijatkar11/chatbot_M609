"""Start Streamlit using the selected profile's configured port."""

import sys
from pathlib import Path

from streamlit.web import cli

from config.settings import settings


def main() -> None:
    app_path = Path(__file__).resolve().parent / "frontend" / "app.py"
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(settings.streamlit_port),
    ]
    cli.main()


if __name__ == "__main__":
    main()
