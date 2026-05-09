# Dr. Bimala Mishra Pathology - Management System

A robust, enterprise-grade Pathology Reporting and Laboratory Information System (LIS) built with Python and Streamlit. This application modernizes pathology workflows by integrating secure data management, PDF report generation, and AI-driven insights.

## Features

- **Role-Based Access Control (RBAC):** Secure login portals tailored for Patients, Pathologists, Technicians, and Receptionists.
- **Patient Portal:** Patients can log in using their UHID to view past history, download approved reports, and interact with an automated Patient Support AI bot.
- **Staff Dashboard:**
  - Enter test results.
  - Generate clinical reports.
  - Automated Billing and Invoicing.
- **Pathologist Workflow:** Approve reports before they are visible to patients. Supports human-in-the-loop review of AI-drafted reports.
- **Professional PDF Generation:** Automatic creation of print-ready PDF reports with test interpretations and dynamic QR codes.
- **Analytics & Triage:** 
  - Analytics Copilot for business insights.
  - Smart Triage Alerts for critical cases.
- **AI Integration:** Includes an AI-powered drafting assistant, intelligent document processing (OCR), and conversational agents for staff and patients.

## Tech Stack

- **Frontend / UI:** Streamlit
- **Backend / Logic:** Python
- **Database:** SQLite with SQLAlchemy ORM
- **Data Handling & Validation:** Pandas, Pydantic
- **PDF Generation:** FPDF
- **QR Codes:** qrcode, Pillow

## Project Structure

- `app.py`: Main Streamlit application and UI routing.
- `database.py`: SQLAlchemy database models and configuration.
- `models.py`: Pydantic schemas for data validation.
- `logic.py`: Core logic for test evaluation and interpretation.
- `ai_service.py`: Integration with AI capabilities (drafting, chatting, analytics).
- `pdf_generator.py`: Logic for creating formatted PDF reports.
- `requirements.txt`: Python dependencies.

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd report
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Start the Streamlit development server by running:

```bash
streamlit run app.py
```

The application will be accessible at `http://localhost:8501`.

## Usage

- **First-time Setup:** Navigate to the Staff Login tab to sign up an initial user (e.g., Receptionist or Pathologist).
- **Patient Registration:** Add a new patient and generate their reports from the main staff dashboard.
- **Approval:** A Pathologist must approve a report in the "Approval Workflow" before it can be downloaded.
- **Billing:** Track payments and dues in the "Billing & Invoices" tab.

## License

All rights reserved.
