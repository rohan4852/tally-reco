# TODO - Fix backend startup

- [ ] Create a plan to resolve `ModuleNotFoundError: No module named 'app.routes'`
- [ ] Update `backend/app/main.py` to import routers from the correct package (likely `routes.*`)
- [ ] Verify imports for `upload`, `health`, `parse` paths
- [ ] Run the server with `uvicorn app.main:app --reload ...` and confirm `/health` and `/docs` work

