# RAKSHA AI Android

Production Android client for RAKSHA AI. This project contains the UI, notification listener/extractor, local history cache, backend API client, device credential storage, and alert delivery. AI inference and threat-intelligence processing remain on the deployed backend.

## Development
- Debug builds default to `http://127.0.0.1:8000/` for a physical phone connected over USB with `adb reverse`. For an Android emulator, override the backend URL with `-PRAKSHA_BACKEND_URL=http://10.0.2.2:8000/`.
- For a physical phone using USB reverse networking, run `adb reverse tcp:8000 tcp:8000` and keep the default URL. For Wi-Fi testing, override the backend URL at build time with `-PRAKSHA_BACKEND_URL=http://YOUR_PC_IP:8000/`.
- Debug builds may use cleartext HTTP. Release builds require HTTPS.
- Set `-PRAKSHA_GOOGLE_WEB_CLIENT_ID=...` only when the legacy Gmail integration is being tested.

## Release
- Set `RAKSHA_BACKEND_URL` to the deployed HTTPS API endpoint.
- Release builds keep the legacy Gmail UI disabled until user-scoped OAuth/token storage is migrated to the production backend.
- Configure Play signing outside the repository; never commit signing keys or `local.properties`.
- Build an Android App Bundle (AAB) for Play Console.

## Architecture
Android UI + Notification Listener + Extractor + Alert Manager -> HTTPS -> RAKSHA FastAPI -> LangGraph -> threat intelligence / Qwen via llama.cpp -> PostgreSQL + Neo4j.

## Privacy/security boundary
The app sends only notification-derived event fields required for analysis. Release networking uses HTTPS and the device bearer credential is encrypted with Android Keystore-backed AES-GCM storage.
