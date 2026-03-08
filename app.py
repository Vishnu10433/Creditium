from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import or_, extract
from datetime import datetime, timedelta, timezone
from flask_babel import Babel, _
from flask import abort

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# IO
from io import StringIO
from io import BytesIO


# Email
import smtplib

# Utils
import csv
import json
import uuid
import io
import os
import random



# ---------------- App setup ----------------
basedir = os.path.abspath(os.path.dirname(__file__))

STATIC_FOLDER = os.path.join(basedir, 'static')

# Do NOT auto create any folders
UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, 'uploads')
KYC_UPLOADS = os.path.join(UPLOAD_FOLDER, 'kyc')
PROFILE_UPLOADS = os.path.join(UPLOAD_FOLDER, 'profiles')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'youremail@gmail.com'       # your gmail
app.config['MAIL_PASSWORD'] = 'your_app_password'         # gmail app password
# ---------------- DB setup ----------------
db_path = os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path + '?check_same_thread=False'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)



def get_locale():
    return session.get('lang', 'en')

babel = Babel(app, locale_selector=get_locale)
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'hi', 'ta', 'te', 'ml']
# ---------------- Models ----------------

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)  # unique
    mobile = db.Column(db.String(30), unique=True, nullable=False)   # unique
    password = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    profile_image = db.Column(db.String(300), nullable=True)
    status = db.Column(db.String(20), default="Pending")

    # Relationships
    wallet = db.relationship('Wallet', backref='user', uselist=False)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    rewards = db.relationship('Reward', backref='user', lazy=True)
    auto_debits = db.relationship('AutoDebit', backref='user', lazy=True)
    kycs = db.relationship('KYC', backref='user', lazy=True)
    loan_applications = db.relationship('LoanApplication', lazy=True)


class Loan(db.Model):
    __tablename__ = 'loan'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    eligibility = db.Column(db.String(100), nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    tenure = db.Column(db.Integer, nullable=False)

    # Relationships
    applications = db.relationship('LoanApplication', backref='loan', lazy=True)


class LoanApplication(db.Model):
    __tablename__ = 'loan_application'
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # ← must come first
    loanname = db.Column(db.String(100))
    amount = db.Column(db.Float, nullable=False)
    tenure = db.Column(db.Integer, nullable=False)
    purpose = db.Column(db.String(200))
    status = db.Column(db.String(50), default="Pending")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    bank_name = db.Column(db.String(150), nullable=True)
    account_number = db.Column(db.String(50), nullable=True)
    ifsc_code = db.Column(db.String(20), nullable=True)
    money_sent = db.Column(db.Boolean, default=False)

    # Relationships — place AFTER all columns
    emis = db.relationship('EMI', backref='loan', lazy=True)
    user = db.relationship('User', foreign_keys='LoanApplication.user_id', overlaps="loan_applications,loan_applications_rel")
class EMI(db.Model):
    __tablename__ = 'emi'
    id = db.Column(db.Integer, primary_key=True)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    emi_amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    paid_on = db.Column(db.DateTime, nullable=True)

    loan_application = db.relationship(
        "LoanApplication",
        overlaps="emis,loan"
    )

    transaction = db.relationship('Transaction', backref='emi', uselist=False)


    
class Wallet(db.Model):
    __tablename__ = 'wallet'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    balance = db.Column(db.Float, default=0.0)

    disbursements = db.relationship('Disbursement', backref='wallet', lazy=True)
    


class Disbursement(db.Model):
    __tablename__ = 'disbursement'
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.id'), nullable=False)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(50), default="Completed")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Transaction(db.Model):
    __tablename__ = "transaction"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'))
    emi_id = db.Column(db.Integer, db.ForeignKey('emi.id'))  # <-- Must exist
    amount = db.Column(db.Float, nullable=False)
    transaction_id = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime)
    type = db.Column(db.String)





class AutoDebit(db.Model):
    __tablename__ = 'auto_debit'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    emi_id = db.Column(db.Integer, db.ForeignKey('emi.id'), nullable=False)
    active = db.Column(db.Boolean, default=True)
    payment_method = db.Column(db.String(50), default='UPI')


class Reward(db.Model):
    __tablename__ = 'reward'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    points = db.Column(db.Integer, default=0)
    description = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class KYC(db.Model):
    __tablename__ = 'kyc'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(200))
    dob = db.Column(db.String(50))
    address = db.Column(db.Text)
    aadhaar = db.Column(db.String(50))
    pan = db.Column(db.String(50))
    live_photo = db.Column(db.String(300))
    id_front = db.Column(db.String(300))
    id_back = db.Column(db.String(300))
    salary_slip = db.Column(db.String(300))
    bank_statement = db.Column(db.String(300))
    status = db.Column(db.String(20), default="Pending")  # Pending / Approved / Rejected
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Ticket(db.Model):
    __tablename__ = 'ticket'
    id = db.Column(db.Integer, primary_key=True)
    issue = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Pending")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)  # <-- Add this

   


class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)  # unique
    mobile = db.Column(db.String(15), unique=True, nullable=False)  # unique
    password = db.Column(db.String(200), nullable=False)
class SupportMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(20))
    message = db.Column(db.Text, nullable=False)
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    user_name = db.Column(db.String(150), nullable=False)
    emi_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="Pending")  # Pending / Reconciled
    date = db.Column(db.DateTime, default=datetime.utcnow)

class UserFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(20))
    message = db.Column(db.Text, nullable=False)
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

# ---------------- Create tables ----------------
app.app_context().push()
db.create_all()
# ---------------- Helpers ----------------
def create_wallet_for_user(user_id):
    if not Wallet.query.filter_by(user_id=user_id).first():
        w = Wallet(user_id=user_id, balance=0.0)
        db.session.add(w)
        db.session.commit()
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def __repr__(self):
        return f"<Notification {self.title} for user {self.user_id}>"
def __repr__(self):
        return f"<SupportMessage {self.name} - {self.email}>"
def send_email(to_email, subject, html_content):
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        sender_email = "yourgmail@gmail.com"
        sender_password = "your-app-password"  # Gmail App Password (not normal password)

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_content, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()

        return True

    except Exception as e:
        print("Email Error:", e)
        return False

def generate_txn_id():
    """Generate a unique transaction id (timezone-aware)."""
    return f"TXN{datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}"

def create_emis_for_loan(loan):
    """
    Create EMI rows for a loan if none exist yet.
    Expects loan to have fields: id, amount, tenure (months).
    Returns number of EMIs created (0 if already existed).
    """
    # use the EMI model from your declared models
    existing = EMI.query.filter_by(loan_application_id=loan.id).first()
    if existing:
        # EMI plan already exists
        return 0

    # Simple equal-split EMI (no interest calculation) — adapt if needed
    if not getattr(loan, "tenure", None) or loan.tenure <= 0:
        # cannot create EMIs without tenure; fallback: single payment
        emi_amount = loan.amount
        emi_count = 1
    else:
        emi_count = int(loan.tenure)
        emi_amount = round((loan.amount / emi_count), 2)

    for i in range(emi_count):
        due_date = datetime.now(timezone.utc) + timedelta(days=30 * (i + 1))
        emi = EMI(
            loan_application_id=loan.id,
            emi_amount=emi_amount,
            due_date=due_date,
            status="Pending"
        )
        db.session.add(emi)

    db.session.commit()
    return emi_count
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash("Admin login required", "danger")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function
# ---------------- Routes ----------------
@app.route('/')
def index():
    return render_template('index.html')




# ----- Register -----
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        age = int(request.form.get('age', 18))
        gender = request.form.get('gender', 'Other')
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        mobile = request.form.get('mobile', '').strip()

        # Handle profile image
        file = request.files.get('profile_image')
        profile_image = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(PROFILE_UPLOADS, filename)
            file.save(file_path)
            # Save relative URL path for rendering in templates
            profile_image = f'/uploads/profiles/{filename}'

        # Basic validation
        if not username or not email or not password:
            flash("Please fill required fields", "danger")
            return redirect(url_for('register'))

        # Check duplicates
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or Email already exists!", "danger")
            return redirect(url_for('register'))

        hashed = generate_password_hash(password)
        user = User(
            username=username,
            email=email,
            password=hashed,
            age=age,
            gender=gender,
            mobile=mobile,
            profile_image=profile_image
        )
        db.session.add(user)
        db.session.commit()

        create_wallet_for_user(user.id)

        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


# ----- Login -----
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            # store user id in session
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f"Welcome, {user.username}!", "success")
            return redirect(url_for('dashboard'))

        flash("Invalid email or password!", "danger")
        return redirect(url_for('login'))

    return render_template('login.html')


# ----- Dashboard -----
@app.route('/set-language', methods=['POST'])
def set_language():
    lang = request.form.get('lang', 'en')
    session['lang'] = lang
    return redirect(request.referrer or url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('login'))

    unread_count = Notification.query.filter_by(user_id=user_id, read=False).count()

    active_loans = 0
    paid_emis = 0
    reward_points = 0

    for app in user.loan_applications:
        if app.status and app.status.strip().lower() in ['approved', 'disbursed']:
            active_loans += 1

        for emi in app.emis:
            if emi.status and emi.status.strip().lower() == 'paid':
                paid_emis += 1

    if hasattr(user, 'reward_points'):
        reward_points = user.reward_points or 0

    return render_template(
        'dashboard.html',
        user=user,
        username=user.username,
        email=user.email,
        age=user.age,
        gender=user.gender,
        mobile=user.mobile,
        unread_count=unread_count,
        active_loans=active_loans,
        paid_emis=paid_emis,
        reward_points=reward_points
    )




@app.route('/credit_rewards')
def credit_rewards():
    # Get logged-in user's ID from session
    user_id = session.get('user_id')  # or 'admin_id' if admin
    if not user_id:
        return redirect('/login')  # user not logged in
    
    # Fetch user from DB
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    # Send data to template
    return render_template(
        'credit_rewards.html',
        credit_score=getattr(user, 'credit_score', 0),
        reward_points=getattr(user, 'reward_points', 0),
        recent_rewards=getattr(user, 'recent_rewards', []),
    )


# ----- Logout -----
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for('index'))


# ----- Loan discovery & application (unchanged) -----
@app.route('/loan-discovery')
def loan_discovery():
    loans = Loan.query.all()
    return render_template('loan-discovery.html', loans=loans)


# Apply Loan Page
@app.route('/applyLoan/<int:loan_id>', methods=['GET'])
def apply_loan_page(loan_id):
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login'))

    loan = Loan.query.get_or_404(loan_id)
    user = db.session.get(User, session['user_id'])


    return render_template('loan_application.html', loan=loan, user=user)


# Submit Loan Application
@app.route('/submitLoanApplication', methods=['POST'])
def submit_application():
    if 'user_id' not in session:
        flash("Please login to apply for a loan", "error")
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    user = User.query.get(user_id)

    # Check KYC
    latest_kyc = user.kycs[-1] if user.kycs else None
    if not latest_kyc or latest_kyc.status != 'Approved':
        flash("You must complete KYC before applying for a loan.", "warning")
        # Save form data in session temporarily
        session['loan_form_data'] = {
            "loan_id": request.form.get('loan_id'),
            "loanname": request.form.get('loanname'),
            "amount": request.form.get('amount'),
            "tenure": request.form.get('tenure'),
            "purpose": request.form.get('purpose')
        }
        return redirect(url_for('kyc_form'))

    # KYC approved → submit application
    application = LoanApplication(
        loan_id=request.form.get('loan_id'),
        user_id=user_id,
        loanname=request.form.get('loanname'),
        amount=float(request.form.get('amount', 0)),
        purpose=request.form.get('purpose'),
        tenure=int(request.form.get('tenure', 0)),
        status='Pending'
    )

    db.session.add(application)
    db.session.commit()

    flash("Loan application submitted and is now Pending approval!", "success")
    return render_template('success.html', application=application)


# Loan Submission after KYC
@app.route('/submitLoanAfterKYC')
def submit_application_after_kyc():
    loan_data = session.pop('loan_form_data', None)
    if not loan_data:
        flash("No loan data found.", "danger")
        return redirect(url_for('loan_discovery'))

    user_id = session.get('user_id')
    application = LoanApplication(
        loan_id=loan_data['loan_id'],
        user_id=user_id,
        loanname=loan_data['loanname'],
        amount=float(loan_data['amount']),
        purpose=loan_data['purpose'],
        tenure=int(loan_data['tenure']),
        status='Pending'
    )
    db.session.add(application)
    db.session.commit()

    flash("Loan application submitted successfully after KYC!", "success")
    return render_template('success.html', application=application)

@app.route('/loan-status')
def loan_status():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    applications = LoanApplication.query.filter_by(user_id=session['user_id']).all()
    return render_template('loan_status.html', applications=applications)

@app.route('/share-bank-details/<int:loan_id>', methods=['GET', 'POST'])
def share_bank_details(loan_id):
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    application = LoanApplication.query.get_or_404(loan_id)

    if application.user_id != session['user_id']:
        flash("You are not allowed to update this loan.", "danger")
        return redirect(url_for('loan_status'))

    if application.status == 'Rejected':
        flash("Bank details cannot be submitted for a rejected loan.", "danger")
        return redirect(url_for('loan_status'))

    if application.money_sent:
        flash("Money has already been disbursed. Bank details cannot be changed.", "warning")
        return redirect(url_for('loan_status'))

    if request.method == 'POST':
        import re
        bank_name      = request.form.get('bank_name', '').strip()
        account_number = request.form.get('account_number', '').strip()
        ifsc_code      = request.form.get('ifsc_code', '').strip().upper()

        errors = []
        if not bank_name:
            errors.append("Bank name is required.")
        if not account_number or not account_number.isdigit() or not (9 <= len(account_number) <= 18):
            errors.append("Account number must be 9–18 digits.")
        if not ifsc_code or not re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', ifsc_code):
            errors.append("IFSC code is invalid. Format: XXXX0XXXXXX")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template('share_bank_details.html', app=application)

        application.bank_name      = bank_name
        application.account_number = account_number
        application.ifsc_code      = ifsc_code

        try:
            db.session.commit()
            flash("Bank details submitted successfully!", "success")
        except Exception as e:
            db.session.rollback()
            print("share_bank_details error:", e)
            flash("Something went wrong. Please try again.", "danger")

        return redirect(url_for('loan_status'))

    return render_template('share_bank_details.html', app=application)



# ----- EMI & Wallet -----
from datetime import datetime, date

@app.route("/emi_schedule")
def emi_schedule():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])

    loan_apps = LoanApplication.query.filter_by(user_id=user.id).all()

    loans = []
    total_emis = paid_emis = pending_emis = overdue_emis = 0

    today = date.today()  # Use date only for comparison

    for loan in loan_apps:
        emis = EMI.query.filter_by(loan_application_id=loan.id).order_by(EMI.due_date).all()

        paid_count = sum(1 for e in emis if e.status == "Paid")
        total_count = len(emis)

        total_emis += total_count
        paid_emis += paid_count

        for e in emis:
            emi_due = e.due_date
            if isinstance(emi_due, datetime):
                emi_due = emi_due.date()  # Convert datetime to date for comparison

            if e.status == "Pending" and emi_due < today:
                overdue_emis += 1
            elif e.status == "Pending":
                pending_emis += 1

        loans.append({
            "loan": loan,
            "emis": emis,
            "paid_count": paid_count
        })

    return render_template(
        "emi_schedule.html",
        loans=loans,
        user=user,
        today=today,
        total_emis=total_emis,
        paid_emis=paid_emis,
        pending_emis=pending_emis,
        overdue_emis=overdue_emis
    )


@app.route("/pay-emi/<int:emi_id>", methods=["POST"], endpoint="pay_emi")
def pay_emi(emi_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    emi = db.session.get(EMI, emi_id)

    if not emi:
        flash("EMI not found!", "danger")
        return redirect(url_for("emi_schedule"))

    if emi.status == "Paid":
        flash("EMI already paid!", "info")
        return redirect(url_for("emi_schedule"))

    if not user.wallet:
        user.wallet = Wallet(user_id=user.id, balance=0)
        db.session.add(user.wallet)
        db.session.commit()

    if user.wallet.balance < emi.emi_amount:
        flash("Insufficient wallet balance!", "danger")
        return redirect(url_for("emi_schedule"))

    try:
        user.wallet.balance -= emi.emi_amount
        emi.status = "Paid"
        emi.paid_on = datetime.now()

        txn = Transaction(
            user_id=user.id,
            loan_application_id=emi.loan_application_id,
            emi_id=emi.id,
            amount=emi.emi_amount,
            transaction_id=generate_txn_id(),
            status="debited",
            timestamp=datetime.now()
        )
        db.session.add(txn)
        db.session.commit()
        flash(f"EMI {emi.id} paid successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error while paying EMI.", "danger")
        print("pay_emi error:", e)

    return redirect(url_for("emi_schedule"))





# ----- Support & notifications -----
@app.route('/notifications')
def notifications_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user = User.query.get(user_id)

    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.timestamp.desc()).all()

    # Count unread notifications
    unread_count = Notification.query.filter_by(user_id=user_id, read=False).count()

    # Mark all as read
    Notification.query.filter_by(user_id=user_id, read=False).update({'read': True})
    db.session.commit()

    return render_template('notifications.html', notifications=notifications, unread_count=unread_count, user=user)


@app.route('/support', methods=['GET'])
def support():
    return render_template('support.html')

@app.route('/support-submit', methods=['POST'])
def support_submit():
    name = request.form.get('name')
    email = request.form.get('email')
    mobile = request.form.get('mobile')
    message = request.form.get('message')

    if not name or not email or not message:
        flash("Please fill in all required fields.", "error")
        return redirect(url_for('support'))

    new_message = SupportMessage(name=name, email=email, mobile=mobile, message=message)
    db.session.add(new_message)
    db.session.commit()

    flash("Your message has been submitted successfully! Our support team will contact you soon.", "success")
    return redirect(url_for('support'))



@app.route('/settings')
def settings():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user = User.query.get(user_id)

    return render_template(
        'settings.html',
        user=user,
        username=user.username,
        email=user.email,
        mobile=user.mobile
    )


# ----- Profile settings (edit) -----
@app.route('/profile-settings')
def profile_settings():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login'))

    user = db.session.get(User, session['user_id'])
    return render_template('profile_settings.html', user=user)


@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login'))

    user = db.session.get(User, session['user_id'])

    # update fields
    user.username = request.form.get('username', user.username).strip()
    user.email = request.form.get('email', user.email).strip().lower()
    user.mobile = request.form.get('mobile', user.mobile).strip()

    # profile image upload
    file = request.files.get('profile_image')
    if file and file.filename:
        filename = secure_filename(file.filename)
        file_path = os.path.join(PROFILE_UPLOADS, filename)
        file.save(file_path)
        user.profile_image = f"profiles/{filename}"

    db.session.commit()

    flash("Profile updated successfully!", "success")

    # ✅ redirect to settings page
    return redirect(url_for('settings'))
# ---------------- Admin Routes ----------------

# ---------------- Admin Registration ----------------

@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if Admin.query.first():
        flash("Admin account already exists! Please login.", "warning")
        return redirect(url_for('admin_login'))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not mobile or not password or not confirm_password:
            flash("All fields are required!", "danger")
            return redirect(url_for('admin_register'))

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('admin_register'))

        hashed_password = generate_password_hash(password)

        new_admin = Admin(
            username=username,
            email=email,
            mobile=mobile,
            password=hashed_password
        )
        db.session.add(new_admin)
        db.session.commit()

        flash("Admin registered successfully! Please login.", "success")
        return redirect(url_for('admin_login'))

    return render_template("admin_register.html")


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        admin = Admin.query.filter_by(email=email).first()

        if admin and check_password_hash(admin.password, password):
            session.clear()
            session['admin_logged_in'] = True
            session['admin_id'] = admin.id
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid credentials", "danger")
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')
# ---------------- Admin Dashboard ----------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    from datetime import timedelta
    today = datetime.now()
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)

    total_users      = User.query.count()
    active_loans     = LoanApplication.query.filter_by(status='Disbursed').count()
    pending_kyc      = KYC.query.filter_by(status='Pending').count()
    overdue_emis     = EMI.query.filter(EMI.status=='Pending', EMI.due_date < today).count()

    disbursed_today  = db.session.query(db.func.sum(LoanApplication.amount))\
                         .filter(LoanApplication.timestamp >= today_start,
                                 LoanApplication.status == 'Disbursed').scalar() or 0

    recent_loans     = LoanApplication.query.order_by(LoanApplication.timestamp.desc()).limit(5).all()

    collected_today  = db.session.query(db.func.sum(EMI.emi_amount))\
                         .filter(EMI.paid_on >= today_start, EMI.status=='Paid').scalar() or 0
    overdue_amount   = db.session.query(db.func.sum(EMI.emi_amount))\
                         .filter(EMI.status=='Pending', EMI.due_date < today).scalar() or 0
    due_today_amount = db.session.query(db.func.sum(EMI.emi_amount))\
                         .filter(EMI.status=='Pending',
                                 EMI.due_date >= today_start,
                                 EMI.due_date < today_start + timedelta(days=1)).scalar() or 0
    pending_tickets  = SupportMessage.query.count()

    return render_template("admin_dashboard.html",
        admin_name       = session.get('admin_username'),
        total_users      = total_users,
        active_loans     = active_loans,
        pending_kyc      = pending_kyc,
        overdue_emis     = overdue_emis,
        disbursed_today  = disbursed_today,
        recent_loans     = recent_loans,
        collected_today  = collected_today,
        overdue_amount   = overdue_amount,
        due_today_amount = due_today_amount,
        pending_tickets  = pending_tickets,
    )


# ---------------- Admin Logout ----------------
@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    return redirect(url_for('admin_login'))





# ---------------- Admin: Users ----------------
@app.route('/admin/users')
def admin_users_list():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    search = request.args.get('q', '').strip()
    if search:
        users = User.query.filter(
            or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.mobile.ilike(f'%{search}%')
            )
        ).order_by(User.id.desc()).all()
    else:
        users = User.query.order_by(User.id.desc()).all()

    # Count users by status
    total_users = User.query.count()
    active_users = User.query.filter_by(status='Verified').count()
    deactive_users = User.query.filter_by(status='Deactivated').count()
    pending_users = User.query.filter_by(status='Pending').count()

    return render_template('admin_users.html',
                           users=users,
                           total_users=total_users,
                           active_users=active_users,
                           deactive_users=deactive_users,
                           pending_users=pending_users,
                           search=search)

@app.route('/admin/users/verify/<int:user_id>')
def admin_verify_user(user_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    user = User.query.get_or_404(user_id)
    user.status = "Verified"
    db.session.commit()
    flash(f"User '{user.username}' has been verified.", "success")
    return redirect(url_for('admin_users_list'))

@app.route('/admin/users/deactivate/<int:user_id>')
def admin_deactivate_user(user_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    user = User.query.get_or_404(user_id)
    user.status = "Deactivated"
    db.session.commit()
    flash(f"User '{user.username}' has been deactivated.", "warning")
    return redirect(url_for('admin_users_list'))

# ---------------- KYC List & Review ----------------
def save_upload_file(file):
    if file and file.filename:
        filename = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + secure_filename(file.filename)
        file_path = os.path.join(KYC_UPLOADS, filename)
        file.save(file_path)
        return filename   # SAVE ONLY THE FILENAME (NOT PATH)
    return None


# ---------------- KYC FORM ----------------
@app.route('/kyc_form', methods=['GET', 'POST'])
def kyc_form():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    existing = KYC.query.filter_by(user_id=user_id).first()

    if request.method == 'POST':
        # Save KYC info
        full_name = request.form.get('full_name')
        dob = request.form.get('dob')
        address = request.form.get('address')
        aadhaar = request.form.get('aadhaar')
        pan = request.form.get('pan')

        # File uploads (optional)
        def save_upload_file(file):
            if file and file.filename:
                filename = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + secure_filename(file.filename)
                file_path = os.path.join(KYC_UPLOADS, filename)
                file.save(file_path)
                return filename
            return None

        live_photo = save_upload_file(request.files.get('live_photo'))
        id_front = save_upload_file(request.files.get('id_front'))
        id_back = save_upload_file(request.files.get('id_back'))
        salary_slip = save_upload_file(request.files.get('salary_slip'))
        bank_statement = save_upload_file(request.files.get('bank_statement'))

        if existing:
            existing.full_name = full_name
            existing.dob = dob
            existing.address = address
            existing.aadhaar = aadhaar
            existing.pan = pan
            if live_photo: existing.live_photo = live_photo
            if id_front: existing.id_front = id_front
            if id_back: existing.id_back = id_back
            if salary_slip: existing.salary_slip = salary_slip
            if bank_statement: existing.bank_statement = bank_statement
            existing.status = "Pending"
            existing.timestamp = datetime.utcnow()
            db.session.commit()
        else:
            k = KYC(
                user_id=user_id,
                full_name=full_name,
                dob=dob,
                address=address,
                aadhaar=aadhaar,
                pan=pan,
                live_photo=live_photo,
                id_front=id_front,
                id_back=id_back,
                salary_slip=salary_slip,
                bank_statement=bank_statement,
                status="Pending",
                timestamp=datetime.utcnow()
            )
            db.session.add(k)
            db.session.commit()

        flash("KYC submitted successfully.", "success")

        # Continue loan application if any
        if session.get('loan_form_data'):
            return redirect(url_for('submit_application_after_kyc'))

        return redirect(url_for('loan_status'))

    return render_template('kyc_form.html', kyc=existing)



# ---------------- File Serving Routes ----------------
@app.route('/uploads/general/<path:filename>')
def serve_general_uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/uploads/kyc/<path:filename>')
def serve_kyc_uploads(filename):
    return send_from_directory(KYC_UPLOADS, filename)


@app.route('/uploads/profiles/<path:filename>')
def serve_profile_uploads(filename):
    return send_from_directory(PROFILE_UPLOADS, filename)



# ---------------- Admin KYC List ----------------
@app.route('/admin/users/kyc_list')
def admin_kyc_list():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    user_id = request.args.get('user_id')

    if user_id:
        kycs = KYC.query.filter_by(user_id=user_id).order_by(KYC.timestamp.desc()).all()
    else:
        kycs = KYC.query.order_by(KYC.timestamp.desc()).all()

    return render_template('admin_kyc_list.html', kycs=kycs)


# ---------------- Admin Review KYC ----------------
@app.route('/admin/loan/review/<int:loan_id>', methods=['GET', 'POST'])
def admin_review_loan(loan_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    loan = LoanApplication.query.get_or_404(loan_id)
    user = User.query.get(loan.user_id)
    kyc = KYC.query.filter_by(user_id=loan.user_id).order_by(KYC.timestamp.desc()).first()

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'approve':
            loan.status = 'Approved'
        elif action == 'reject':
            loan.status = 'Rejected'
        db.session.commit()
        flash(f"Loan ID {loan.id} has been {loan.status}.", "success")
        return redirect(url_for('admin_loans_history'))

    return render_template('admin_loan_review.html', loan=loan, user=user, kyc=kyc)

# ---------------- Admin Review KYC ----------------
@app.route('/admin/kyc/<int:kyc_id>', methods=['GET', 'POST'])
def admin_review_kyc(kyc_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    kyc = db.session.get(KYC, kyc_id)
    if not kyc:
        abort(404)

    user = db.session.get(User, kyc.user_id)
    if not user:
        abort(404)

    if request.method == 'POST':
        action = request.form.get('action')

        latest_loan = LoanApplication.query.filter_by(
            user_id=kyc.user_id,
            status='Pending'
        ).order_by(LoanApplication.id.desc()).first()

        if action == 'approve':
            kyc.status = 'Approved'
            if latest_loan:
                latest_loan.status = 'Approved'
            db.session.commit()
            flash(f"KYC for {user.username} approved and loan auto-approved.", "success")

        elif action == 'reject':
            kyc.status = 'Rejected'
            if latest_loan:
                latest_loan.status = 'Rejected'
            db.session.commit()
            flash(f"KYC for {user.username} rejected and loan auto-rejected.", "warning")

        return redirect(url_for('admin_kyc_list'))

    return render_template('admin_kyc_review.html', kyc=kyc, user=user)

# -------------- CONTINUE YOUR NEXT ROUTE --------------
@app.route('/admin/users/deactivate')
def deactivate_users():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    # Fetch all users with status 'Deactivated'
    users = User.query.filter_by(status='Deactivated').order_by(User.id.desc()).all()
    return render_template('deactivate_users.html', users=users)


# ---------------- Admin Advance Search ----------------
@app.route('/admin/users/search', methods=['GET'])
def admin_users_search():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    search_query = request.args.get('q', '').strip()

    if search_query:
        users = User.query.filter(
            or_(
                User.username.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%'),
                User.mobile.ilike(f'%{search_query}%')
            )
        ).order_by(User.id.desc()).all()
    else:
        users = []

    return render_template('advance_search.html', users=users, search=search_query)
@app.route('/admin/users/export')

@app.route('/admin/users/export_full')
def admin_users_export_full():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    users = User.query.order_by(User.id.desc()).all()

    # Create in-memory CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        'User ID', 'Username', 'Email', 'Mobile', 'Status', 'Registered On',
        'Full Name', 'DOB', 'Address', 'Aadhaar', 'PAN',
        'Live Photo', 'ID Front', 'ID Back', 'Salary Slip', 'Bank Statement', 'KYC Status', 'KYC Submitted On'
    ])

    # Data rows
    for u in users:
        kyc = KYC.query.filter_by(user_id=u.id).order_by(KYC.timestamp.desc()).first()
        writer.writerow([
            u.id,
            u.username,
            u.email,
            u.mobile,
            u.status,
            u.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(u, 'created_at') else '',
            kyc.full_name if kyc else '',
            kyc.dob if kyc else '',
            kyc.address if kyc else '',
            kyc.aadhaar if kyc else '',
            kyc.pan if kyc else '',
            kyc.live_photo if kyc else '',
            kyc.id_front if kyc else '',
            kyc.id_back if kyc else '',
            kyc.salary_slip if kyc else '',
            kyc.bank_statement if kyc else '',
            kyc.status if kyc else '',
            kyc.timestamp.strftime("%Y-%m-%d %H:%M:%S") if kyc else ''
        ])

    output.seek(0)
    return Response(output,
                    mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=users_kyc_export.csv"})

@app.route('/admin/admin_user_bank_details')
def admin_user_bank_details():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    # Order by newest first so newly shared bank details appear at top
    all_loans = LoanApplication.query.order_by(LoanApplication.id.desc()).all()
    loans = [
        l for l in all_loans
        if l.bank_name and l.bank_name.strip() and l.bank_name.strip() != 'None'
        and l.account_number and l.account_number.strip() and l.account_number.strip() != 'None'
        and l.ifsc_code and l.ifsc_code.strip() and l.ifsc_code.strip() != 'None'
    ]

    today = date.today()
    return render_template('admin_user_bank_details.html', loans=loans, today=today)


@app.route('/admin/send-money/<int:loan_id>', methods=['POST'])
def admin_send_money(loan_id):
    # protect admin route
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    # prefer modern db.session.get where available
    loan = db.session.get(LoanApplication, loan_id)
    if not loan:
        flash("Loan not found!", "danger")
        return redirect(url_for('admin_user_bank_details'))

    if getattr(loan, "money_sent", False):
        flash("Money already sent for this loan.", "warning")
        return redirect(url_for('admin_user_bank_details'))

    try:
        user = db.session.get(User, loan.user_id)
        if not user:
            flash("User not found for this loan!", "danger")
            return redirect(url_for('admin_user_bank_details'))

        # Ensure wallet record exists
        wallet = Wallet.query.filter_by(user_id=user.id).first()
        if not wallet:
            wallet = Wallet(user_id=user.id, balance=0.0)
            db.session.add(wallet)
            db.session.flush()  # optional to make it visible in same transaction

        # Credit wallet
        wallet.balance = (wallet.balance or 0.0) + float(loan.amount)

        # Mark loan as disbursed
        loan.money_sent = True
        loan.status = "Disbursed"
        loan.timestamp = datetime.now(timezone.utc)

        # Create a disbursement/transaction record
        txn = Transaction(
            user_id=user.id,
            loan_application_id=loan.id,
            amount=float(loan.amount),
            transaction_id=generate_txn_id(),
            status="credited",
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(txn)

        db.session.commit()  # commit wallet, loan, txn first

        # Create EMIs AFTER commit so DB relationships are stable
        created_count = create_emis_for_loan(loan)
        if created_count:
            flash(f"Money sent and EMI plan ({created_count} EMIs) created.", "success")
        else:
            flash("Money sent successfully (EMI plan already existed).", "success")

    except Exception as e:
        db.session.rollback()
        print("admin_send_money error:", e)
        flash("Error while sending money.", "danger")

    return redirect(url_for('admin_user_bank_details'))


# ------------------ WALLET PAGE ------------------
@app.route('/wallet')
def wallet_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    wallet = Wallet.query.filter_by(user_id=user_id).first()
    balance = wallet.balance if wallet else 0

    transactions = Transaction.query.filter_by(
        user_id=user_id
    ).order_by(Transaction.timestamp.desc()).all()

    return render_template(
        'wallet.html',
        wallet={"balance": balance},
        transactions=transactions
    )


# ------------------ ADD FUNDS (MANUAL CREDIT) ------------------
@app.route('/add_funds', methods=['POST'])
def add_funds():
    if 'user_id' not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    amount = float(request.form.get('amount'))

    wallet = Wallet.query.filter_by(user_id=user_id).first()
    if not wallet:
        wallet = Wallet(user_id=user_id, balance=0)

    wallet.balance += amount

    # Create transaction record
    transaction = Transaction(
        user_id=user_id,
        loan_application_id=None,
        amount=amount,
        status="Credited",
        transaction_id=str(random.randint(111111, 999999))
    )

    db.session.add(transaction)
    db.session.commit()

    flash("Funds added successfully!", "success")
    return redirect(url_for('wallet_page'))

# ---------------- DOWNLOAD PDF STATEMENT ----------------
@app.route('/download_statement')
def download_statement():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.timestamp.desc()).all()

    file_path = os.path.join("static", "statements")
    os.makedirs(file_path, exist_ok=True)
    pdf_file = os.path.join(file_path, f"statement_{user_id}.txt")

    with open(pdf_file, "w", encoding="utf-8") as file:
        file.write("Transaction Statement\n")
        file.write("=====================\n\n")
        for tx in transactions:
            line = f"{tx.timestamp} - {tx.status.upper()} - ₹{tx.amount}\n"
            file.write(line)

    return send_file(pdf_file, as_attachment=True)


# ------------------ WITHDRAW ------------------
@app.route('/withdraw', methods=['POST'])
def withdraw_money():
    if 'user_id' not in session:
        flash("Login required!", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    bank_name = request.form.get('bank_name')
    account_number = request.form.get('account_number')
    ifsc_code = request.form.get('ifsc_code')
    amount = float(request.form.get('amount'))

    wallet = Wallet.query.filter_by(user_id=user_id).first()

    if not wallet or wallet.balance < amount:
        flash("Insufficient wallet balance!", "danger")
        return redirect(url_for('wallet_page'))

    wallet.balance -= amount

    tx = Transaction(
        user_id=user_id,
        loan_application_id=None,
        amount=amount,
        status="Debited",
        transaction_id=str(random.randint(111111, 999999))
    )
    db.session.add(tx)
    db.session.commit()

    # EMAIL
    subject = "Withdrawal Successful — LoanApp"
    message_html = f"""
        <p>Hello {user.username},</p>
        <p>Your withdrawal request of <strong>₹{amount:.2f}</strong> has been processed.</p>
        <p><b>Bank:</b> {bank_name}<br>
        <b>Account:</b> {account_number}<br>
        <b>IFSC:</b> {ifsc_code}</p>
        <p>If you didn't make this request, contact support immediately.</p>
        <p>Thank you,<br>LoanApp Team</p>
    """

    send_email(user.email, subject, message_html)

    flash("Withdrawal successful!", "success")
    return redirect(url_for('wallet_page'))


@app.route('/admin/loans/status')
def admin_loans_status():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    loans = LoanApplication.query.all()
    # Add computed fields for template
    for loan in loans:
        loan.paid_count = sum(1 for emi in loan.emis if emi.status == 'Paid')
        loan.pending_count = sum(1 for emi in loan.emis if emi.status == 'Pending' and emi.due_date >= datetime.now())
        loan.overdue_count = sum(1 for emi in loan.emis if emi.status == 'Pending' and emi.due_date < datetime.now())
    return render_template('admin_loans_status.html', loans=loans)


@app.route('/admin/loans/approve')
def admin_loans_approve():
    approved_loans = LoanApplication.query.filter_by(status='Approved').all()
    rejected_loans = LoanApplication.query.filter_by(status='Rejected').all()
    pending_loans = LoanApplication.query.filter_by(status='Pending').all()

    return render_template(
        'admin_loans_approve.html',
        approved_loans=approved_loans,
        rejected_loans=rejected_loans,
        pending_loans=pending_loans
    )
@app.route('/admin/loans/analytics')
def admin_loans_analytics():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    # Total loan applications
    total_loans = LoanApplication.query.count()

    # Approved, Rejected, Pending counts
    approved = LoanApplication.query.filter_by(status='Approved').count()
    rejected = LoanApplication.query.filter_by(status='Rejected').count()
    pending = LoanApplication.query.filter_by(status='Pending').count()

    # Total amount requested by users
    total_amount_requested = db.session.query(
        db.func.sum(LoanApplication.amount)
    ).scalar() or 0

    # Total amount approved (only from approved loans)
    total_amount_approved = db.session.query(
        db.func.sum(LoanApplication.amount)
    ).filter(LoanApplication.status == 'Approved').scalar() or 0

    # Count how many users received money (money_sent=True)
    total_disbursed = LoanApplication.query.filter_by(money_sent=True).count()

    return render_template(
        "admin_loan_analytics.html",
        total_loans=total_loans,
        approved=approved,
        rejected=rejected,
        pending=pending,
        total_amount_requested=total_amount_requested,
        total_amount_approved=total_amount_approved,
        total_disbursed=total_disbursed
    )
@app.route('/admin/payments')
def admin_payments():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    payments = db.session.query(
        EMI.id,
        User.username,
        User.email,
        LoanApplication.loanname,
        EMI.emi_amount,
        EMI.due_date,
        EMI.status,
        EMI.paid_on
    ).join(LoanApplication, EMI.loan_application_id == LoanApplication.id)\
     .join(User, LoanApplication.user_id == User.id)\
     .all()

    return render_template("admin_payments.html", payments=payments)

@app.route('/admin/payments/collections')
def admin_collections():

    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    # All PAID EMIs
    paid_emis = (
        db.session.query(
            EMI.id.label("emi_id"),
            EMI.emi_amount,
            EMI.due_date,
            EMI.paid_on,
            User.username,
            LoanApplication.loanname
        )
        .join(LoanApplication, EMI.loan_application_id == LoanApplication.id)
        .join(User, LoanApplication.user_id == User.id)
        .filter(EMI.status == "Paid")
        .all()
    )

    # Summary totals
    total_collected = sum([p.emi_amount for p in paid_emis])
    total_paid_count = len(paid_emis)

    # Prepare chart data for last 12 months
    

    monthly_labels = []
    monthly_values = []

    from datetime import datetime
    now = datetime.now()

    for i in range(12):
        month = (now.month - i - 1) % 12 + 1
        year = now.year - ((now.month - i - 1) // 12)

        monthly_labels.append(f"{month}/{year}")

        month_total = (
            db.session.query(db.func.sum(EMI.emi_amount))
            .filter(
                EMI.status == "Paid",
                extract("year", EMI.paid_on) == year,
                extract("month", EMI.paid_on) == month
            )
            .scalar() or 0
        )

        monthly_values.append(month_total)

    monthly_labels.reverse()
    monthly_values.reverse()

    return render_template(
        "admin_collections.html",
        paid_emis=paid_emis,
        total_collected=total_collected,
        total_paid_count=total_paid_count,
        month_labels=monthly_labels,
        month_values=monthly_values
    )
@app.route('/admin/payments/overdue')
def admin_overdue_payments():

    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    today = date.today()

    payments = (
        db.session.query(
            EMI.id.label("emi_id"),
            EMI.emi_amount,
            EMI.due_date,
            User.username,
            User.email,
            LoanApplication.loanname
        )
        .join(LoanApplication, EMI.loan_application_id == LoanApplication.id)
        .join(User, LoanApplication.user_id == User.id)
        .filter(
            EMI.status == "Pending",
            EMI.due_date < datetime.now()     # overdue
        )
        .all()
    )

    return render_template(
        "admin_overdue_payments.html",
        payments=payments,
        today=today
    )

@app.route('/admin/payments/reminders')
def payment_reminders_page():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    emis = EMI.query.order_by(EMI.due_date).all()
    return render_template('admin_reminders.html', emis=emis, now=datetime.now())
# ---------------------------
# Send Reminder to ALL Users
# ---------------------------
@app.route('/admin/payments/send_all', methods=['POST'])
def send_all_reminders():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    pending_emis = EMI.query.filter_by(status='Pending').all()
    count = 0

    for emi in pending_emis:
        user = emi.loan_application.user
        notif = Notification(
            title="Payment Reminder",
            message=f"Your EMI of ₹{emi.emi_amount} is due on {emi.due_date.strftime('%d %b %Y')}.",
            user_id=user.id
        )
        db.session.add(notif)
        count += 1

    db.session.commit()
    flash(f"Payment reminders sent to {count} users!", "success")
    return redirect(url_for('payment_reminders_page'))

# ---------------------------
# Send Reminder for Single EMI
# ---------------------------
@app.route('/admin/payments/send/<int:emi_id>', methods=['POST'])
def send_single_reminder(emi_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    emi = EMI.query.get_or_404(emi_id)
    user = emi.loan_application.user
    notif = Notification(
        title="Payment Reminder",
        message=f"Your EMI of ₹{emi.emi_amount} is due on {emi.due_date.strftime('%d %b %Y')}.",
        user_id=user.id
    )
    db.session.add(notif)
    db.session.commit()
    flash(f"Reminder sent to {user.username} for EMI ID {emi.id}!", "success")
    return redirect(url_for('payment_reminders_page'))

# ---------------------------
# Reverse Payment
# ---------------------------
@app.route('/admin/payments/reverse/<int:emi_id>', methods=['POST'])
def reverse_payment(emi_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    emi = EMI.query.get_or_404(emi_id)
    emi.status = 'Pending'
    emi.paid_on = None
    db.session.commit()
    flash(f"Payment for EMI ID {emi.id} has been reversed.", "warning")
    return redirect(url_for('payment_reminders_page'))

        
@app.route('/admin/payments/reconcile')
@admin_required
def admin_payments_reconcile():
    payments = Payment.query.order_by(Payment.date.desc()).all()
    return render_template('admin_reconcile.html', payments=payments)

@app.route('/admin/payments/reconcile/<int:payment_id>/mark', methods=['POST'])
@admin_required
def mark_payment_reconciled(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    payment.status = 'Reconciled'
    db.session.commit()
    flash(f"Payment for {payment.user_name} marked as Reconciled!", "success")
    return redirect(url_for('admin_payments_reconcile'))


@app.route('/admin/payments/reports')
@admin_required
def admin_payments_reports():
    payments = Payment.query.order_by(Payment.date.desc()).all()
    return render_template('admin_reports.html', payments=payments)


@app.route('/admin/payments/export_csv')
@admin_required
def export_payments_csv():
    payments = Payment.query.order_by(Payment.date.desc()).all()

    output = BytesIO()
    csv_data = []

    # Header
    csv_data.append(['ID', 'User', 'EMI Amount', 'Status', 'Date'])

    # Rows
    for p in payments:
        csv_data.append([
            p.id,
            p.user_name or "Unknown",                                        # ✅ fixed: was p.user.name
            p.emi_amount,                                                     # ✅ fixed: was p.amount
            p.status,
            p.date.strftime("%Y-%m-%d %H:%M:%S") if p.date else ""          # ✅ fixed: null-safe
        ])

    text_buffer = ""
    for row in csv_data:
        text_buffer += ",".join(map(str, row)) + "\n"

    output.write(text_buffer.encode('utf-8'))
    output.seek(0)

    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name="payment_report.csv"
    )



@app.route('/admin/support/tickets')
def admin_support_tickets():
    if 'admin_logged_in' not in session:
        return redirect('/admin/login')

    # Use the correct field name
    messages = SupportMessage.query.order_by(SupportMessage.date_submitted.desc()).all()
    return render_template('admin_support_tickets.html', messages=messages)


@app.route('/admin/send_notifications', methods=['GET', 'POST'])
@admin_required  # use your existing admin auth decorator
def admin_send_notifications():
    # fetch users for dropdown
    users = User.query.all()

    if request.method == 'POST':
        user_id = request.form.get('user_id')  # empty string if all users
        title = request.form.get('title')
        message = request.form.get('message')

        if not title or not message:
            flash("Title and message cannot be empty", "danger")
            return redirect(url_for('admin_send_notifications'))

        if user_id:
            # Send to a specific user
            notification = Notification(user_id=int(user_id), title=title, message=message)
            db.session.add(notification)
        else:
            # Send to all users
            for user in users:
                notification = Notification(user_id=user.id, title=title, message=message)
                db.session.add(notification)

        db.session.commit()
        flash("Notification sent successfully!", "success")
        return redirect(url_for('admin_send_notifications'))

    return render_template('admin_send_notifications.html', users=users)


@app.route('/userfeedback')
def user_feedback():
    return render_template('userfeedback.html')

# Route to handle form submission
@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    name = request.form.get('name')
    email = request.form.get('email')
    mobile = request.form.get('mobile')
    message = request.form.get('message')

    if not name or not email or not message:
        flash("Please fill in all required fields!", "danger")
        return redirect(url_for('user_feedback'))

    feedback = UserFeedback(
        name=name,
        email=email,
        mobile=mobile,
        message=message
    )

    db.session.add(feedback)
    db.session.commit()

    flash("Your feedback has been submitted successfully!", "success")
    return redirect(url_for('user_feedback'))  # <-- THIS LINE IS MISSING BEFORE


# Admin view for feedback
@app.route('/admin/feedback')
@admin_required
def admin_feedback():
    feedbacks = UserFeedback.query.order_by(UserFeedback.date_submitted.desc()).all()
    return render_template('admin_feedback.html', feedbacks=feedbacks)

# Mark feedback as read
@app.route('/admin/feedback/read/<int:feedback_id>')
@admin_required
def mark_feedback_read(feedback_id):
    feedback = UserFeedback.query.get_or_404(feedback_id)
    feedback.is_read = True
    db.session.commit()
    flash(f"Feedback ID {feedback.id} marked as read.", "success")
    return redirect(url_for('admin_feedback'))

# Delete feedback
@app.route('/admin/feedback/delete/<int:feedback_id>')
@admin_required
def delete_feedback(feedback_id):
    feedback = UserFeedback.query.get_or_404(feedback_id)
    db.session.delete(feedback)
    db.session.commit()
    flash(f"Feedback ID {feedback.id} deleted.", "success")
    return redirect(url_for('admin_feedback'))


@app.route('/admin/loans/history')
def admin_loans_history():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    money_sent = request.args.get('money_sent', '')

    query = LoanApplication.query.join(User)

    if search:
        query = query.filter(User.username.ilike(f"%{search}%"))

    if status:
        query = query.filter(LoanApplication.status == status)

    if money_sent != "":
        query = query.filter(LoanApplication.money_sent == (money_sent == "1"))

    loans = query.order_by(LoanApplication.timestamp.desc()).paginate(page=page, per_page=10)

    return render_template("admin_loan_history.html", loans=loans)
@app.route('/admin/loan/<int:loan_id>')
def admin_view_loan(loan_id):
    loan = LoanApplication.query.get_or_404(loan_id)
    return render_template("admin_loan_review.html", loan=loan)



@app.route('/admin/debug-bank')
def debug_bank():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    loans = LoanApplication.query.all()
    result = "<h2>All Loans Bank Data</h2>"
    for l in loans:
        result += f"<p>ID:{l.id} | bank='{l.bank_name}' | acc='{l.account_number}' | ifsc='{l.ifsc_code}' | status='{l.status}'</p>"
    return result

@app.route('/admin/managers')
@app.route('/admin/loans')



@app.route('/admin/loans/assign')


@app.route('/admin/reports/dashboard')
@app.route('/admin/reports/export')
@app.route('/admin/reports/performance')
@app.route('/admin/roles')
@app.route('/admin/logs')
@app.route('/admin/security/alerts')
@app.route('/admin/reports/regional')
@app.route('//admin/reports/trends')
@app.route('/admin/reports/custom')
@app.route('/admin/send_notifications')
@app.route('/admin/announcements')
def placeholder_routes():
    return "<h2>Page coming soon...</h2>"
# ---------------- Run + init ----------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if Loan.query.count() == 0:
            sample_loans = [
                Loan(name="Personal Loan", eligibility="Salary > 25k/month", interest_rate=12.5, tenure=24),
                Loan(name="Home Loan", eligibility="Salary > 50k/month", interest_rate=8.5, tenure=120),
                Loan(name="Car Loan", eligibility="Salary > 30k/month", interest_rate=10.0, tenure=60)
            ]
            db.session.bulk_save_objects(sample_loans)
            db.session.commit()

    app.run(debug=True)
