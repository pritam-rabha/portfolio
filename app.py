from flask import Flask, render_template, request, redirect, session, send_from_directory
import psycopg2
import os
from werkzeug.security import check_password_hash
from flask import flash

ADMIN_USERNAME = "pritam"
ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$Oog09zPBI4KygGSF$fd271d0200448c63407c4284aae8ad36a799e5231f422efef0adaf0c24a63c5348d1ed07d1a49a4cd3510eddfae8ebdf7eefba36ded1fecf0cf943f63c4d9444"


app = Flask(__name__)
app.secret_key = "supersecretkey123"

# PostgreSQL Config
DB_CONFIG = {
    "host": "localhost",
    "database": "portfolio_db",
    "user": "pritam",
    "password": "p7r7i4t8@"
}

def get_db():
    return psycopg2.connect(**DB_CONFIG)

# Create contacts table
def create_table():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id SERIAL PRIMARY KEY,
            name TEXT,
            email TEXT,
            message TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

create_table()

# Routes
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/projects")
def projects():
    return render_template("projects.html")

@app.route("/resume")
def resume():
    return send_from_directory("static/resume", "Pritam_Resume.pdf", as_attachment=True)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO contacts (name,email,message) VALUES (%s,%s,%s)",
            (name, email, message)
        )
        conn.commit()
        cur.close()
        conn.close()

        return render_template("success.html")

    return render_template("contact.html")



if __name__ == "__main__":
    app.run()

# Admin Login
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session["admin"] = True
            flash("Login successful!", "success")
            return redirect("/admin")

        flash("Invalid username or password", "danger")

    return render_template("login.html")



# Admin Dashboard
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name,email,message FROM contacts ORDER BY id DESC")
    data = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("admin.html", messages=data)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 86400

