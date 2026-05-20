# TODO - Make Streamlit ready to test

- [x] Fix FastAPI router import/startup so `uvicorn app.main:app` works
- [x] Add/verify frontend dependencies spec (Streamlit) or run-commands instructions
- [x] Provide exact run sequence:
  - start `streamlit run main.py`
  - if using a separate backend, set Streamlit `API_BASE_URL` to your running API
- [ ] Quick smoke-test endpoints (`/health`, upload -> reconcile -> download`)

## Notes

- Use `main.py` as the Streamlit entrypoint for the project root.
- A local backend is started automatically when `API_BASE_URL` is not set.
