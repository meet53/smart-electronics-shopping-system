# Smart Electronics Shopping System

Full college project: Flask REST API + MySQL + responsive web app + Flutter Android app.

## Backend
1. Install MySQL and import `backend/schema.sql`.
2. Edit credentials and `SECRET_KEY` in `backend/app.py`.
3. `cd backend && python -m venv venv`
4. Activate venv, then `pip install -r requirements.txt`
5. Run `python app.py`; API runs on `http://127.0.0.1:5000`.

## Web
Open `web/index.html` through a local server, for example `cd web && python -m http.server 5500`. Change `API` in `web/app.js` if needed.

## Flutter
`cd mobile && flutter pub get && flutter run`. For Android emulator use `http://10.0.2.2:5000`; for a physical phone use the computer's LAN IP.

Demo admin: `admin@smartshop.com` / `admin123`.
