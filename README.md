# Church of Pentecost English Service

This is the Python Django workspace for the Church of Pentecost, New Kyekyere District English Service website.

- Live website: https://church-of-pentecost-english-service.vercel.app
- Source code: https://github.com/JET-KII/church-of-pentecost-english-service

The application includes public church information, sermons and events, email-verified member accounts, private member requests, and a staff content dashboard.

## Setup

Create or use the existing virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the development server:

```powershell
python manage.py runserver
```

## Production configuration

Production requires `DJANGO_SECRET_KEY`, `DATABASE_URL`, `DJANGO_DEBUG=false`, and the approved host/origin values. Public registration remains disabled until a real SMTP service is configured with `EMAIL_HOST` and its related credentials.

Local databases, uploaded media, logs, virtual environments, environment files, and Vercel metadata are excluded from source control.
