"""Top-level FastAPI application package.

This package exists so `uvicorn app.main:app` can resolve `app.*` imports.
Routers live in the sibling top-level `routes/` package, so imports in
`app.main` must reference `routes.*`.
"""