from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from datetime import datetime
import sqlite3, os, uuid

app = Flask(__name__)
CORS(app)

DB = "tickets.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id          TEXT PRIMARY KEY,
                ticket_num  INTEGER NOT NULL,
                full_name   TEXT NOT NULL,
                contact     TEXT NOT NULL,
                email       TEXT,
                service     TEXT NOT NULL,
                pref_date   TEXT,
                pref_time   TEXT,
                message     TEXT,
                status      TEXT DEFAULT 'pending',
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ticket_counter (
                id    INTEGER PRIMARY KEY,
                value INTEGER DEFAULT 1000
            )
        """)
        row = conn.execute("SELECT * FROM ticket_counter WHERE id=1").fetchone()
        if not row:
            conn.execute("INSERT INTO ticket_counter VALUES (1, 1000)")
        conn.commit()

def next_ticket():
    with get_db() as conn:
        conn.execute("UPDATE ticket_counter SET value = value + 1 WHERE id=1")
        conn.commit()
        row = conn.execute("SELECT value FROM ticket_counter WHERE id=1").fetchone()
        return row["value"]

# ── Public: appointment form ───────────────────────────────────────────────────
@app.route("/appointment")
def appointment_form():
    return render_template("appointment.html")

@app.route("/appointment/submit", methods=["POST"])
def submit_appointment():
    data = request.form
    now  = datetime.now().isoformat(timespec="seconds")
    tid  = str(uuid.uuid4())
    tnum = next_ticket()

    with get_db() as conn:
        conn.execute("""
            INSERT INTO appointments
              (id, ticket_num, full_name, contact, email, service,
               pref_date, pref_time, message, status, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,'pending',?,?)
        """, (tid, tnum,
              data.get("full_name","").strip(),
              data.get("contact","").strip(),
              data.get("email","").strip(),
              data.get("service","").strip(),
              data.get("pref_date","").strip(),
              data.get("pref_time","").strip(),
              data.get("message","").strip(),
              now, now))
        conn.commit()

    return redirect(url_for("ticket_confirmation", ticket_num=tnum))

@app.route("/appointment/confirmation/<int:ticket_num>")
def ticket_confirmation(ticket_num):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM appointments WHERE ticket_num=?", (ticket_num,)
        ).fetchone()
    if not row:
        return "Ticket not found", 404
    return render_template("confirmation.html", ticket=dict(row))

# ── Admin: dashboard ───────────────────────────────────────────────────────────
@app.route("/admin")
@app.route("/admin/dashboard")
def admin_dashboard():
    return render_template("admin.html")

# ── API: list tickets (admin polling) ─────────────────────────────────────────
@app.route("/api/tickets")
def api_tickets():
    status = request.args.get("status", "all")
    search = request.args.get("q", "").strip()
    with get_db() as conn:
        query  = "SELECT * FROM appointments WHERE 1=1"
        params = []
        if status != "all":
            query += " AND status=?"
            params.append(status)
        if search:
            query += " AND (full_name LIKE ? OR ticket_num LIKE ?)"
            params += [f"%{search}%", f"%{search}%"]
        query += " ORDER BY created_at DESC"
        rows = conn.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])

# ── API: update ticket status ──────────────────────────────────────────────────
@app.route("/api/tickets/<ticket_id>/status", methods=["PATCH"])
def update_status(ticket_id):
    body   = request.get_json()
    status = body.get("status")
    if status not in ("pending","confirmed","done","cancelled"):
        return jsonify({"error": "invalid status"}), 400
    now = datetime.now().isoformat(timespec="seconds")
    with get_db() as conn:
        conn.execute(
            "UPDATE appointments SET status=?, updated_at=? WHERE id=?",
            (status, now, ticket_id)
        )
        conn.commit()
    return jsonify({"ok": True})

# ── API: stats ─────────────────────────────────────────────────────────────────
@app.route("/api/stats")
def api_stats():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT status, COUNT(*) as cnt FROM appointments GROUP BY status
        """).fetchall()
        total = conn.execute("SELECT COUNT(*) as c FROM appointments").fetchone()["c"]
    counts = {r["status"]: r["cnt"] for r in rows}
    return jsonify({
        "total":     total,
        "pending":   counts.get("pending",   0),
        "confirmed": counts.get("confirmed", 0),
        "done":      counts.get("done",      0),
        "cancelled": counts.get("cancelled", 0),
    })

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
