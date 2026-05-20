from pathlib import Path
import sys
import os
import logging
from threading import Thread

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
BACKEND_PATH = ROOT / "backend"
BACKEND_APP_PATH = BACKEND_PATH / "app"

# Setup Python path for imports
paths_to_add = [
    str(ROOT),
    str(BACKEND_PATH),
    str(BACKEND_APP_PATH),
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)
        logger.info(f"Added to sys.path: {path}")

_LOCAL_API_THREAD_STARTED = False


def _start_local_api_if_needed() -> None:
    """Start the FastAPI backend in a daemon thread if API_BASE_URL is not set."""
    global _LOCAL_API_THREAD_STARTED
    if _LOCAL_API_THREAD_STARTED:
        return

    api_base_url = os.environ.get("API_BASE_URL")
    if api_base_url:
        logger.info(f"Using external API_BASE_URL: {api_base_url}")
        return

    logger.info("Starting local FastAPI backend...")
    try:
        import uvicorn
        logger.info("uvicorn imported successfully")
        
        # Try to import the FastAPI app
        from app.main import app as fastapi_app
        logger.info("FastAPI app imported successfully")
        
        def _run_api() -> None:
            """Run the FastAPI server."""
            try:
                logger.info("Starting uvicorn server on 127.0.0.1:8000")
                uvicorn.run(
                    fastapi_app,
                    host="127.0.0.1",
                    port=8000,
                    log_level="warning"
                )
            except Exception as e:
                logger.error(f"Error running FastAPI server: {e}", exc_info=True)

        thread = Thread(target=_run_api, daemon=True)
        thread.start()
        _LOCAL_API_THREAD_STARTED = True
        logger.info("FastAPI backend thread started successfully")
        
    except ImportError as e:
        logger.warning(f"Could not import FastAPI backend: {e}")
        logger.warning("Frontend will use API_BASE_URL from environment if available")
    except Exception as e:
        logger.error(f"Unexpected error starting backend: {e}", exc_info=True)


def main() -> None:
    """Main entry point for the Streamlit app."""
    _start_local_api_if_needed()
    
    try:
        from frontend.app import main as app_main
        logger.info("Frontend app imported successfully")
        app_main()
    except ImportError as e:
        logger.error(f"Could not import frontend app: {e}", exc_info=True)
        import streamlit as st
        st.error(f"Failed to load frontend: {e}")
        st.info("Make sure the frontend/app module exists and is properly configured")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}", exc_info=True)
        import streamlit as st
        st.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
