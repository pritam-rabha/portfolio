from flask import Flask, render_template, request, redirect, session, send_from_directory, flash
import psycopg2
from werkzeug.security import check_password_hash
import smtplib
from email.message import EmailMessage
import threading
from flask import render_template_string
import os




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


EMAIL_ADDRESS = "pritamrba@gmail.com"
EMAIL_PASSWORD = "auoy gdtq clfh vgsv"



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




def send_email_notification(name, email, message):
    try:
        html = render_template(
            "email/contact_email.html",
            name=name,
            email=email,
            message=message
        )

        msg = EmailMessage()
        msg["Subject"] = "📩 New Portfolio Contact Message"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = EMAIL_ADDRESS   # YOU

        msg.set_content("New message received")
        msg.add_alternative(html, subtype="html")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

    except Exception as e:
        print("Admin email failed:", e)


def send_reply_email(to_email, reply, original_message):
    try:
        html = render_template(
            "email/reply_email.html",
            reply=reply,
            original_message=original_message
        )

        msg = EmailMessage()
        msg["Subject"] = "Reply from Pritam"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg["Cc"] = EMAIL_ADDRESS   # 🔥 CC YOURSELF

        msg.set_content(reply)
        msg.add_alternative(html, subtype="html")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

    except Exception as e:
        print("Reply email failed:", e)


    except Exception as e:
        print("Client reply failed:", e)








# ======================
# PUBLIC ROUTES
# ======================

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

        # Save to DB
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO contacts (name,email,message) VALUES (%s,%s,%s)",
            (name, email, message)
        )
        conn.commit()
        cur.close()
        conn.close()

        # 🔥 SEND EMAIL IN BACKGROUND
        threading.Thread(
            target=send_email_notification,
            args=(name, email, message),
            daemon=True
        ).start()

        return render_template("success.html")

    return render_template("contact.html")


# ======================
# ADMIN AUTH
# ======================

@app.route("/login", methods=["GET", "POST"])
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

@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
SELECT id, name, email, message, replied
FROM contacts
ORDER BY id DESC
""")

    data = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("admin.html", messages=data)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ======================
# ERROR HANDLERS
# ======================

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500

# ======================
# RUN APP (MUST BE LAST)
# ======================



@app.route("/reply/<int:id>/<email>", methods=["POST"])
def reply(id, email):
    if not session.get("admin"):
        return redirect("/login")

    reply_text = request.form.get("reply")

    conn = get_db()
    cur = conn.cursor()

    # get original message
    cur.execute("SELECT message FROM contacts WHERE id=%s", (id,))
    original_message = cur.fetchone()[0]

    # send reply email
    send_reply_email(email, reply_text, original_message)

    # save reply in DB
    cur.execute("""
        UPDATE contacts
        SET replied = TRUE,
            reply_text = %s,
            replied_at = NOW()
        WHERE id = %s
    """, (reply_text, id))

    conn.commit()
    cur.close()
    conn.close()

    flash("Reply sent and saved", "success")
    return redirect("/admin")


@app.route("/delete/<int:id>", methods=["POST"])
def delete_message(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM contacts WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()

    flash("Message deleted successfully", "danger")
    return redirect("/admin")





if __name__ == "__main__":
    app.run()
