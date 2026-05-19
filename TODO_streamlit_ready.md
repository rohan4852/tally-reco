# TODO - Make Streamlit ready to test

- [ ] Fix FastAPI router import/startup so `uvicorn app.main:app` works
- [ ] Add/verify frontend dependencies spec (Streamlit) or run-commands instructions
- [ ] Provide exact run sequence:
  - start backend
  - set Streamlit `API_BASE_URL`
  - start `streamlit run frontend/app.py`
- [ ] Quick smoke-test endpoints (`/health`, upload -> reconcile -> download`)
