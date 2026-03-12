from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3, math

app = Flask(__name__)
app.secret_key = "ride_secret"

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("ride.db", check_same_thread=False)

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        source TEXT,
        destination TEXT,
        lat REAL,
        lng REAL,
        travel_date TEXT,
        travel_time TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user INTEGER,
        to_user INTEGER,
        message TEXT
    )
    """)

    conn.commit()

init_db()

# ---------------- UTILS ----------------
def distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        conn = get_db()
        conn.execute("INSERT INTO users VALUES (NULL,?,?,?)",
                     (request.form["name"], request.form["email"], request.form["password"]))
        conn.commit()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=? AND password=?",
                            (request.form["email"], request.form["password"])).fetchone()
        if user:
            session["user_id"] = user[0]
            session["name"] = user[1]
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    matches = []

    if request.method == "POST":
        lat = float(request.form["lat"])
        lng = float(request.form["lng"])

        conn.execute(
            "INSERT INTO trips VALUES (NULL,?,?,?,?,?,?,?)",
            (session["user_id"],
             request.form["source"],
             request.form["destination"],
             lat, lng,
             request.form["date"],
             request.form["time"])
        )
        conn.commit()

        trips = conn.execute("SELECT * FROM trips WHERE user_id != ?", (session["user_id"],)).fetchall()

        for t in trips:
            d = distance(lat, lng, t[4], t[5])
            if d <= 10:
                matches.append(t)

    return render_template("dashboard.html", matches=matches, name=session["name"])

@app.route("/chat/<int:user_id>", methods=["GET","POST"])
def chat(user_id):
    conn = get_db()

    if request.method == "POST":
        conn.execute("INSERT INTO chat VALUES (NULL,?,?,?)",
                     (session["user_id"], user_id, request.form["message"]))
        conn.commit()

    messages = conn.execute("""
    SELECT * FROM chat
    WHERE (from_user=? AND to_user=?)
    OR (from_user=? AND to_user=?)
    """, (session["user_id"], user_id, user_id, session["user_id"])).fetchall()

    return render_template("chat.html", messages=messages)

app.run(debug=True)
