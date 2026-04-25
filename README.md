# HJMP Malolos – Appointment Ticketing System

## What this system does
- Parishioners fill out the **appointment form** on your website
- Each submission gets a **ticket number** automatically
- Parish staff see all tickets in real time on the **admin dashboard**
- Staff can mark tickets as Confirmed → Done, or Cancel them

---

## Setup (run once)

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Run the server
python app.py
```

The server starts at **http://localhost:5000**

---

## Pages

| URL | Who uses it |
|-----|-------------|
| `http://localhost:5000/appointment` | Public – parishioners book here |
| `http://localhost:5000/admin` | Staff – ticketing dashboard |

---

## How to add to your existing website (Figma → real site)

When your website is live, replace your **"Book Appointment"** button link with:
```
http://your-domain.com/appointment
```

Or embed the form in an `<iframe>`:
```html
<iframe src="http://your-domain.com/appointment" width="100%" height="800px" frameborder="0"></iframe>
```

---

## Deploying to a real server (so everyone can access it)

Options:
- **PythonAnywhere** (free tier available) – upload files, set `app.py` as the WSGI file
- **Railway / Render** – connect your GitHub repo, auto-deploys
- **VPS (DigitalOcean, Linode)** – run with `gunicorn app:app --bind 0.0.0.0:5000`

---

## Ticket flow

```
Parishioner submits form
        ↓
  Status: PENDING  ← staff sees this immediately
        ↓
  Staff calls/contacts parishioner
        ↓
  Status: CONFIRMED
        ↓
  Appointment day arrives
        ↓
  Status: DONE
```

---

## Database
Uses SQLite (`tickets.db`) – created automatically when you first run `app.py`.
No setup needed. To view raw data: `sqlite3 tickets.db "SELECT * FROM appointments;"`
