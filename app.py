from flask import Flask, render_template, request, redirect, session
import os
import bcrypt

from werkzeug.utils import secure_filename
import sqlite3

conn = sqlite3.connect(
    'vendor_portal.db',
    check_same_thread=False
)

cursor = conn.cursor()

# ==========================================
# FLASK APP
# ==========================================

app = Flask(__name__)

app.secret_key = "vendor_secret_key"

# ==========================================
# DATABASE CONNECTION
# ==========================================



cursor = conn.cursor()

# ==========================================
# FILE UPLOAD CONFIGURATION
# ==========================================

UPLOAD_FOLDER = 'static/uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ==========================================
# HOME PAGE
# ==========================================

@app.route('/')

def home():

    return render_template('index.html')

# ==========================================
# REGISTER
# ==========================================

@app.route('/register', methods=['GET', 'POST'])

def register():

    message = ""

    if request.method == 'POST':

        name = request.form['name']

        email = request.form['email']

        password = request.form['password']

        role = request.form['role']

        # ==================================
        # ENCRYPT PASSWORD
        # ==================================

        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        )

        try:

            sql = """
            INSERT INTO users
            (name, email, password, role)

            VALUES (%s, %s, %s, %s)
            """

            values = (
                name,
                email,
                hashed_password.decode('utf-8'),
                role
            )

            cursor.execute(sql, values)

            conn.commit()

            return redirect('/login')

        except:

            message = "Email already exists"

    return render_template(
        'register.html',
        message=message
    )

# ==========================================
# LOGIN
# ==========================================

@app.route('/login', methods=['GET', 'POST'])

def login():

    message = ""

    if request.method == 'POST':

        email = request.form['email']

        password = request.form['password']

        # ==================================
        # GET USER USING EMAIL
        # ==================================

        sql = """
        SELECT * FROM users
        WHERE email=%s
        """

        values = (email,)

        cursor.execute(sql, values)

        user = cursor.fetchone()

        # ==================================
        # CHECK PASSWORD
        # ==================================

        if user:

            stored_password = user[3]

            if bcrypt.checkpw(
                password.encode('utf-8'),
                stored_password.encode('utf-8')
            ):

                session['name'] = user[1]

                session['role'] = user[4]

                return redirect('/dashboard')

            else:

                message = "Invalid Password"

        else:

            message = "User not found"

    return render_template(
        'login.html',
        message=message
    )

# ==========================================
# DASHBOARD
# ==========================================

@app.route('/dashboard')

def dashboard():

    if 'name' not in session:

        return redirect('/login')

    cursor.execute("SELECT COUNT(*) FROM vendors")

    total_vendors = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM vendors
    WHERE risk_level='High'
    """)

    high_risk = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM vendors
    WHERE risk_level='Medium'
    """)

    medium_risk = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM vendors
    WHERE risk_level='Low'
    """)

    low_risk = cursor.fetchone()[0]

    return render_template(
        'dashboard.html',
        name=session.get('name'),
        total_vendors=total_vendors,
        high_risk=high_risk,
        medium_risk=medium_risk,
        low_risk=low_risk
    )

# ==========================================
# ADD VENDOR
# ==========================================

@app.route('/add_vendor', methods=['GET', 'POST'])

def add_vendor():

    if 'name' not in session:

        return redirect('/login')

    if request.method == 'POST':

        company_name = request.form['company_name']

        service_type = request.form['service_type']

        risk_level = request.form['risk_level']

        status = request.form['status']

        # ==================================
        # FILE UPLOAD
        # ==================================

        file = request.files['document']

        filename = ""

        if file and file.filename != '':

            filename = secure_filename(file.filename)

            file.save(
                os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    filename
                )
            )

        # ==================================
        # INSERT VENDOR
        # ==================================

        sql = """
        INSERT INTO vendors
        (company_name, service_type, risk_level, status)

        VALUES (%s, %s, %s, %s)
        """

        values = (
            company_name,
            service_type,
            risk_level,
            status
        )

        cursor.execute(sql, values)

        conn.commit()

        vendor_id = cursor.lastrowid

        # ==================================
        # SAVE DOCUMENT
        # ==================================

        if filename != "":

            doc_sql = """
            INSERT INTO documents
            (vendor_id, document_name, file_path)

            VALUES (%s, %s, %s)
            """

            doc_values = (
                vendor_id,
                filename,
                f"static/uploads/{filename}"
            )

            cursor.execute(doc_sql, doc_values)

            conn.commit()

        return redirect('/vendors')

    return render_template('add_vendor.html')

# ==========================================
# VIEW VENDORS
# ==========================================

@app.route('/vendors')

def vendors():

    if 'name' not in session:

        return redirect('/login')

    cursor.execute("SELECT * FROM vendors")

    vendor_data = cursor.fetchall()

    return render_template(
        'vendors.html',
        vendors=vendor_data
    )

# ==========================================
# DOCUMENTS
# ==========================================

@app.route('/documents')

def documents():

    if 'name' not in session:

        return redirect('/login')

    cursor.execute("SELECT * FROM documents")

    docs = cursor.fetchall()

    return render_template(
        'documents.html',
        documents=docs
    )

# ==========================================
# DELETE VENDOR
# ==========================================

@app.route('/delete_vendor/<int:id>')

def delete_vendor(id):

    sql = """
    DELETE FROM vendors
    WHERE vendor_id=%s
    """

    values = (id,)

    cursor.execute(sql, values)

    conn.commit()

    return redirect('/vendors')

# ==========================================
# LOGOUT
# ==========================================

@app.route('/logout')

def logout():

    session.clear()

    return redirect('/login')

# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == '__main__':

    app.run(debug=True)