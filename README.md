# 💳 Creditium — Loan Management System

A full-stack web application for managing loans, EMIs, KYC verification, and user wallets — built with Flask and PostgreSQL.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-Latest-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-blue)
![License](https://img.shields.io/badge/License-Educational-orange)

---

## 🚀 Features

### 👤 User Side
- User Registration & Login with Profile Image
- KYC Submission (Aadhaar, PAN, Live Photo, ID Proof, Salary Slip, Bank Statement)
- Loan Discovery & Application
- EMI Schedule & Payment via Wallet
- Wallet — Add Funds, Withdraw, Transaction History
- PDF Statement Download
- Notifications & Payment Reminders
- Support Tickets & User Feedback
- Bank Details Submission for Disbursement
- Multi-language Support (English, Hindi, Tamil, Telugu, Malayalam)
- Credit Score & Rewards

### 🛡️ Admin Side
- Admin Dashboard with Live Stats
- User Management (Verify / Deactivate / Search / Export CSV)
- KYC Review & Approval / Rejection
- Loan Application Review (Approve / Reject)
- Loan Disbursement to User Wallet
- Bank Details Management
- EMI Tracking (Paid / Pending / Overdue)
- Payment Collections with Monthly Chart
- Overdue Payments Management
- Payment Reminders (Single & Bulk)
- Reverse Payments
- Payment Reconciliation & Reports
- Support Ticket Management
- User Feedback Management
- Send Notifications to Users / All Users
- Loan Analytics Dashboard
- Loan History with Filters & Pagination
- Export Payments as CSV

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Flask |
| Database | PostgreSQL 17 |
| ORM | SQLAlchemy (Flask-SQLAlchemy) |
| Auth | Werkzeug Password Hashing |
| PDF | ReportLab |
| Email | SMTP (Gmail) |
| i18n | Flask-Babel |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Fonts | Google Fonts (DM Sans, Playfair Display) |
| Environment | python-dotenv |

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/Vishnu10433/Creditium.git
cd Creditium
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up PostgreSQL

Open psql and run:
```sql
CREATE DATABASE loanapp_db;
CREATE USER loanapp_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE loanapp_db TO loanapp_user;
\c loanapp_db
GRANT ALL ON SCHEMA public TO loanapp_user;
\q
```

### 5. Create `.env` file
Create a `.env` file in the root directory:
```
DATABASE_URL=postgresql://loanapp_user:yourpassword@localhost:5432/loanapp_db
SECRET_KEY=your_secret_key
```

### 6. Run the app
```bash
python app.py
```

Visit `http://127.0.0.1:5000`

---

## 📁 Project Structure

```
Creditium/
├── app.py                        # Main Flask application
├── requirements.txt              # Python dependencies
├── README.md                     # Project documentation
├── .env                          # Environment variables (not pushed)
├── .gitignore
│
├── static/
│   ├── style.css                 # Global styles
│   ├── script.js                 # Global scripts
│   ├── statements/               # Generated PDF statements
│   └── uploads/
│       ├── kyc/                  # KYC document uploads
│       └── profiles/             # Profile image uploads
│
└── templates/
    ├── index.html                # Landing page
    ├── login.html                # User login
    ├── register.html             # User registration
    ├── dashboard.html            # User dashboard
    ├── loan-discovery.html       # Browse loans
    ├── loan_application.html     # Apply for loan
    ├── loan_status.html          # Check loan status
    ├── emi_schedule.html         # EMI schedule & payment
    ├── wallet.html               # Wallet & transactions
    ├── kyc_form.html             # KYC submission
    ├── share_bank_details.html   # Bank details form
    ├── notifications.html        # User notifications
    ├── support.html              # Support page
    ├── userfeedback.html         # User feedback
    ├── settings.html             # User settings
    ├── credit_rewards.html       # Credit score & rewards
    ├── success.html              # Success page
    ├── reward.html               # Rewards page
    │
    ├── admin_login.html              # Admin login
    ├── admin_register.html           # Admin registration
    ├── admin_dashboard.html          # Admin dashboard
    ├── admin_users.html              # User management
    ├── admin_kyc_list.html           # KYC list
    ├── admin_kyc_review.html         # KYC review
    ├── admin_loans_approve.html      # Loan applications
    ├── admin_loans_status.html       # Loan status
    ├── admin_loan_history.html       # Loan history
    ├── admin_loan_review.html        # Loan review
    ├── admin_loan_analytics.html     # Loan analytics
    ├── admin_user_bank_details.html  # Bank details
    ├── admin_payments.html           # Payments
    ├── admin_collections.html        # Collections
    ├── admin_overdue_payments.html   # Overdue payments
    ├── admin_reminders.html          # Payment reminders
    ├── admin_reconcile.html          # Reconciliation
    ├── admin_reports.html            # Reports
    ├── admin_feedback.html           # Feedback management
    ├── admin_support_tickets.html    # Support tickets
    ├── admin_send_notifications.html # Send notifications
    ├── advance_search.html           # Advanced user search
    └── deactivate_users.html         # Deactivated users
```

---

## 🔐 Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Flask session secret key |

---

## 📌 Key Routes

### User Routes
| Route | Description |
|---|---|
| `/` | Landing page |
| `/register` | User registration |
| `/login` | User login |
| `/dashboard` | User dashboard |
| `/loan-discovery` | Browse available loans |
| `/applyLoan/<id>` | Apply for a loan |
| `/loan-status` | Check loan status |
| `/emi_schedule` | View & pay EMIs |
| `/wallet` | Wallet & transactions |
| `/kyc_form` | Submit KYC documents |
| `/notifications` | View notifications |
| `/support` | Contact support |

### Admin Routes
| Route | Description |
|---|---|
| `/admin_login` | Admin login |
| `/admin/dashboard` | Admin dashboard |
| `/admin/users` | Manage users |
| `/admin/users/kyc_list` | KYC submissions |
| `/admin/loans/approve` | Review loan applications |
| `/admin/loans/history` | Loan history |
| `/admin/loans/analytics` | Loan analytics |
| `/admin/payments` | Payment management |
| `/admin/payments/collections` | Collections & chart |
| `/admin/payments/overdue` | Overdue payments |
| `/admin/payments/reminders` | Send reminders |
| `/admin/feedback` | User feedback |
| `/admin/support/tickets` | Support tickets |
| `/admin/send_notifications` | Send notifications |

---

## 🗄️ Database Models

| Model | Description |
|---|---|
| `User` | Registered users |
| `Admin` | Admin accounts |
| `Loan` | Available loan products |
| `LoanApplication` | User loan applications |
| `EMI` | EMI schedule per loan |
| `Wallet` | User wallet balances |
| `Transaction` | All transactions |
| `Disbursement` | Loan disbursements |
| `KYC` | KYC documents & status |
| `Notification` | User notifications |
| `Ticket` | Support tickets |
| `SupportMessage` | Support messages |
| `Reward` | User reward points |
| `AutoDebit` | Auto debit settings |
| `Payment` | Payment records |
| `UserFeedback` | User feedback |

---

## 👨‍💻 Author

**Vishnu** — [GitHub](https://github.com/Vishnu10433)

---

## 📄 License

This project is built for educational purposes.
