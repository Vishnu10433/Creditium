💳 Creditium — Loan Management System
A full-stack web application for managing loans, EMIs, KYC verification, and user wallets — built with Flask and PostgreSQL.

🚀 Features
👤 User Side

User Registration & Login with Profile Image
KYC Submission (Aadhaar, PAN, Live Photo, ID Proof, Salary Slip, Bank Statement)
Loan Discovery & Application
EMI Schedule & Payment via Wallet
Wallet — Add Funds, Withdraw, Transaction History
PDF Statement Download
Notifications & Payment Reminders
Support Tickets & User Feedback
Bank Details Submission for Disbursement
Multi-language Support (English, Hindi, Tamil, Telugu, Malayalam)
Credit Score & Rewards

🛡️ Admin Side

Admin Dashboard with Live Stats
User Management (Verify / Deactivate / Search / Export CSV)
KYC Review & Approval / Rejection
Loan Application Review (Approve / Reject)
Loan Disbursement to User Wallet
Bank Details Management
EMI Tracking (Paid / Pending / Overdue)
Payment Collections with Monthly Chart
Overdue Payments Management
Payment Reminders (Single & Bulk)
Reverse Payments
Payment Reconciliation & Reports
Support Ticket Management
User Feedback Management
Send Notifications to Users / All Users
Loan Analytics Dashboard
Loan History with Filters & Pagination
Export Payments as CSV


🛠️ Tech Stack
LayerTechnologyBackendPython 3.12, FlaskDatabasePostgreSQL 17ORMSQLAlchemy (Flask-SQLAlchemy)AuthWerkzeug Password HashingPDFReportLabEmailSMTP (Gmail)i18nFlask-BabelFrontendHTML5, CSS3, Vanilla JavaScriptFontsGoogle Fonts (DM Sans, Playfair Display)Environmentpython-dotenv

⚙️ Installation & Setup
1. Clone the repository
bashgit clone https://github.com/Vishnu10433/Creditium.git
cd Creditium
2. Create a virtual environment
bashpython -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
3. Install dependencies
bashpip install -r requirements.txt
4. Set up PostgreSQL
Open psql and run:
sqlCREATE DATABASE loanapp_db;
CREATE USER loanapp_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE loanapp_db TO loanapp_user;
\c loanapp_db
GRANT ALL ON SCHEMA public TO loanapp_user;
\q
5. Create .env file
Create a .env file in the root directory:
DATABASE_URL=postgresql://loanapp_user:yourpassword@localhost:5432/loanapp_db
SECRET_KEY=your_secret_key
6. Run the app
bashpython app.py
Visit http://127.0.0.1:5000

📁 Project Structure
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

🔐 Environment Variables
VariableDescriptionDATABASE_URLPostgreSQL connection stringSECRET_KEYFlask session secret key

📌 Key Routes
User Routes
RouteDescription/Landing page/registerUser registration/loginUser login/dashboardUser dashboard/loan-discoveryBrowse available loans/applyLoan/<id>Apply for a loan/loan-statusCheck loan status/emi_scheduleView & pay EMIs/walletWallet & transactions/kyc_formSubmit KYC documents/notificationsView notifications/supportContact support
Admin Routes
RouteDescription/admin_loginAdmin login/admin/dashboardAdmin dashboard/admin/usersManage users/admin/users/kyc_listKYC submissions/admin/loans/approveReview loan applications/admin/loans/historyLoan history/admin/loans/analyticsLoan analytics/admin/paymentsPayment management/admin/payments/collectionsCollections & chart/admin/payments/overdueOverdue payments/admin/payments/remindersSend reminders/admin/feedbackUser feedback/admin/support/ticketsSupport tickets/admin/send_notificationsSend notifications

🗄️ Database Models
ModelDescriptionUserRegistered usersAdminAdmin accountsLoanAvailable loan productsLoanApplicationUser loan applicationsEMIEMI schedule per loanWalletUser wallet balancesTransactionAll transactionsDisbursementLoan disbursementsKYCKYC documents & statusNotificationUser notificationsTicketSupport ticketsSupportMessageSupport messagesRewardUser reward pointsAutoDebitAuto debit settingsPaymentPayment recordsUserFeedbackUser feedback

👨‍💻 Author
Vishnu — GitHub

📄 License
This project is built for educational purposes.
