from pathlib import Path
import sys
import os
import logging
from threading import Thread
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
BACKEND_PATH = ROOT / "backend"

# Setup Python path for imports - CRITICAL for Streamlit Cloud
# Must add backend to path so that 'from app.x import y' works
paths_to_add = [
    str(BACKEND_PATH),  # For 'from app.x' imports
    str(ROOT),           # For 'from frontend.x' imports
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)
        logger.info(f"Added to sys.path: {path}")


# Module-level guard (works within a single Streamlit process).
_LOCAL_API_THREAD_STARTED = False


def _start_local_api_if_needed() -> None:
    """Start the FastAPI backend in a daemon thread if API_BASE_URL is not set.

    Streamlit can rerun the script on interactions; however we must avoid binding
    the same port multiple times.
    """
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
        # After adding backend to sys.path, this should work
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
        # Give the API a moment to start
        time.sleep(1)
        
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
