import streamlit as st
import pandas as pd
import base64
import os
import io
import qrcode
from datetime import datetime
from pydantic import ValidationError

from logic import evaluate_result, generate_interpretation
from database import init_db, SessionLocal, PatientDB, ReportDB, TestResultDB, TestConfigDB, TestParameterDB, UserDB, AuditLogDB, InvoiceDB, AIJobDB, DocumentDB, ChatContextDB, hash_password, verify_password
from models import PatientSchema
from pdf_generator import create_pdf
from ai_service import generate_ai_report_draft, extract_data_from_document, chat_with_patient_bot, chat_with_staff_rag, generate_smart_triage_alerts, generate_analytics_insights
import json
import base64

# Initialize database
init_db()

# --- DB HELPERS ---
def get_test_options():
    db = SessionLocal()
    try:
        tests = db.query(TestConfigDB).all()
        return [t.name for t in tests] if tests else []
    finally:
        db.close()

def get_test_price(test_name):
    db = SessionLocal()
    try:
        test = db.query(TestConfigDB).filter(TestConfigDB.name == test_name).first()
        return test.price if test else 0.0
    finally:
        db.close()

def get_test_params(test_name):
    db = SessionLocal()
    try:
        test = db.query(TestConfigDB).filter(TestConfigDB.name == test_name).first()
        if not test: return []
        params = db.query(TestParameterDB).filter(TestParameterDB.test_config_id == test.id).all()
        return [{
            "Investigation": p.investigation,
            "Ref_Min": p.ref_min,
            "Ref_Max": p.ref_max,
            "Unit": p.unit
        } for p in params]
    finally:
        db.close()

def log_audit_event(user_id, action, entity_type, details=""):
    db = SessionLocal()
    try:
        log = AuditLogDB(user_id=user_id, action=action, entity_type=entity_type, details=details)
        db.add(log)
        db.commit()
    finally:
        db.close()

def get_base64_of_bin_file(bin_file):
    if not os.path.exists(bin_file):
        return ""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def generate_qr_base64(data):
    if not data:
        data = "UNKNOWN"
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f766e", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Dr. Bimala Mishra Pathology", layout="wide", page_icon="🩺")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Outfit:wght@400;500;600;700&display=swap');

    :root {
        --primary: #0f766e;
        --accent: #14b8a6;
        --bg-gradient: linear-gradient(135deg, #f5fbfb 0%, #eef7f8 100%);
        --card-bg: rgba(255, 255, 255, 0.95);
        --text-main: #0f172a;
        --text-muted: #64748b;
        --border-color: #dbeafe;
    }

    .stApp > header {
        background-color: transparent !important;
    }
    div[data-testid="stAppViewContainer"] {
        background: var(--bg-gradient);
        font-family: 'Inter', sans-serif;
        color: var(--text-main);
    }
    
    h1, h2, h3, h4, h5, h6, .lab-title, .section-title {
        font-family: 'Outfit', sans-serif !important;
        color: var(--primary) !important;
        letter-spacing: 0.5px;
    }

    .report-header {
        background: var(--card-bg);
        backdrop-filter: blur(10px);
        padding: 25px;
        border-top: 6px solid var(--primary);
        border-radius: 0 0 16px 16px;
        margin-bottom: 25px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.025);
        border: 1px solid rgba(255,255,255,0.4);
    }
    .lab-title {
        font-size: 32px;
        font-weight: 700;
        margin: 0;
    }
    .lab-tagline {
        color: var(--accent);
        font-size: 15px;
        font-weight: 500;
        margin-bottom: 10px;
        letter-spacing: 1px;
    }
    .lab-contact {
        font-size: 13px;
        color: var(--text-muted);
        line-height: 1.6;
    }
    .placeholder-box {
        border: 2px dashed var(--border-color);
        border-radius: 12px;
        padding: 20px 30px;
        text-align: center;
        color: var(--text-muted);
        font-size: 12px;
        background-color: rgba(255,255,255,0.5);
        transition: all 0.3s ease;
    }
    
    .section-card {
        background: var(--card-bg);
        backdrop-filter: blur(10px);
        padding: 25px;
        border-radius: 16px;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
        border: 1px solid rgba(255,255,255,0.6);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .section-title {
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 20px;
        border-bottom: 2px solid var(--border-color);
        padding-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
        border-radius: 8px !important;
        border: 1px solid var(--border-color) !important;
        background-color: #ffffff !important;
    }
    div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.2) !important;
    }
    
    button[kind="primary"], .stDownloadButton > button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--border-color);
    }
    
    .stMetric > div {
        background-color: rgba(255,255,255,0.8);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid var(--border-color);
    }
</style>
""", unsafe_allow_html=True)

def color_status(val):
    if 'Critical' in str(val):
        color = '#8b0000' 
        font_weight = 'bold'
    elif 'High' in str(val):
        color = '#cc0000' 
        font_weight = 'bold'
    elif 'Low' in str(val):
        color = '#d35400' 
        font_weight = 'bold'
    else:
        color = '#27ae60' 
        font_weight = 'normal'
    return f'color: {color}; font-weight: {font_weight};'

def init_session_state():
    if "patient_data" not in st.session_state:
        st.session_state.patient_data = {
            "name": "John Doe",
            "uhid": "UHID-100293",
            "age": 45,
            "gender": "Male",
            "ref_doc": "Dr. A. Smith",
            "sample_loc": "Main Lab",
            "collection_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "report_time": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    if "report_generated" not in st.session_state:
        st.session_state.report_generated = False
    if "test_results" not in st.session_state:
        st.session_state.test_results = {}
    
    test_opts = get_test_options()
    if "selected_tests" not in st.session_state:
        st.session_state.selected_tests = [test_opts[0]] if test_opts else []

def save_to_database(patient_data, test_type, results_data, user_id, price, discount, paid_amount, payment_mode):
    db = SessionLocal()
    try:
        patient = db.query(PatientDB).filter(PatientDB.uhid == patient_data.uhid).first()
        if not patient:
            patient = PatientDB(
                uhid=patient_data.uhid,
                name=patient_data.name,
                age=patient_data.age,
                gender=patient_data.gender
            )
            db.add(patient)
            db.flush() 
        else:
            patient.name = patient_data.name
            patient.age = patient_data.age
            patient.gender = patient_data.gender
            
        report = ReportDB(
            patient_id=patient.id,
            test_type=test_type,
            ref_doctor=patient_data.ref_doc,
            sample_loc=patient_data.sample_loc,
            collection_time=patient_data.collection_time,
            report_time=patient_data.report_time,
            status="Result Entered",
            created_by_id=user_id
        )
        db.add(report)
        db.flush()
        
        for res in results_data:
            tr = TestResultDB(
                report_id=report.id,
                investigation=res['Investigation'],
                value=float(res['Result']),
                status=res['Status'],
                reference_range=res['Reference Value'],
                unit=res['Unit']
            )
            db.add(tr)
            
        inv_status = "Paid" if (paid_amount >= (price - discount)) else "Partial" if paid_amount > 0 else "Unpaid"
        inv = InvoiceDB(
            patient_id=patient.id,
            report_id=report.id,
            total_amount=price,
            discount=discount,
            paid_amount=paid_amount,
            payment_mode=payment_mode,
            status=inv_status
        )
        db.add(inv)
        db.flush()
        
        # Trigger AI Job
        ai_output = generate_ai_report_draft(test_type, results_data)
        ai_job = AIJobDB(
            job_type="REPORT_DRAFT",
            status="REQUIRES_REVIEW",
            target_entity_id=report.id,
            input_payload=json.dumps({"test_type": test_type, "results": results_data}),
            output_payload=ai_output
        )
        db.add(ai_job)
        
        db.commit()
        log_audit_event(user_id, "CREATE", "Report&Invoice", f"Created report/invoice for {patient_data.uhid} - {test_type}")
        return True
    except Exception as e:
        db.rollback()
        st.error(f"Database error: {str(e)}")
        return False
    finally:
        db.close()

def check_auth():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.markdown("<div style='text-align: center; margin-top: 50px;'><h1 style='color: #0f766e;'>Secure Pathology Portal</h1></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            tab1, tab2 = st.tabs(["Patient Access", "Staff Login"])
            
            with tab1:
                with st.form("patient_login"):
                    st.markdown("### Access Your Reports")
                    uhid_input = st.text_input("Enter UHID (e.g. UHID-100293)")
                    pat_submit = st.form_submit_button("View Reports", type="primary", use_container_width=True)
                    if pat_submit:
                        db = SessionLocal()
                        try:
                            patient = db.query(PatientDB).filter(PatientDB.uhid == uhid_input).first()
                            if patient:
                                st.session_state.authenticated = True
                                st.session_state.user_id = patient.id
                                st.session_state.user_role = "Patient"
                                st.session_state.user_name = patient.name
                                st.session_state.uhid = patient.uhid
                                st.rerun()
                            else:
                                st.error("UHID not found.")
                        finally:
                            db.close()

            with tab2:
                auth_mode = st.radio("Mode", ["Login", "Sign Up", "Forgot Password"], horizontal=True, label_visibility="collapsed")
                
                if auth_mode == "Login":
                    with st.form("staff_login"):
                        st.markdown("### Authorized Personnel Login")
                        username = st.text_input("Username")
                        password = st.text_input("Password", type="password")
                        submit = st.form_submit_button("Login", type="primary", use_container_width=True)
                        
                        if submit:
                            db = SessionLocal()
                            try:
                                user = db.query(UserDB).filter(UserDB.username == username).first()
                                if user and verify_password(password, user.password_hash):
                                    st.session_state.authenticated = True
                                    st.session_state.user_id = user.id
                                    st.session_state.user_role = user.role
                                    st.session_state.user_name = user.name
                                    log_audit_event(user.id, "LOGIN", "System", "User logged in")
                                    st.rerun()
                                else:
                                    st.error("Invalid username or password.")
                            finally:
                                db.close()
                                
                elif auth_mode == "Sign Up":
                    with st.form("staff_signup"):
                        st.markdown("### Register New Staff")
                        new_name = st.text_input("Full Name")
                        new_username = st.text_input("Choose Username")
                        new_password = st.text_input("Choose Password", type="password")
                        role = st.selectbox("Role", ["Pathologist", "Technician", "Receptionist"])
                        submit_signup = st.form_submit_button("Sign Up", type="primary", use_container_width=True)
                        
                        if submit_signup:
                            if new_username and new_password and new_name:
                                db = SessionLocal()
                                try:
                                    existing = db.query(UserDB).filter(UserDB.username == new_username).first()
                                    if existing:
                                        st.error("Username already exists.")
                                    else:
                                        new_user = UserDB(username=new_username, password_hash=hash_password(new_password), role=role, name=new_name)
                                        db.add(new_user)
                                        db.commit()
                                        st.success("Account created successfully! Please switch to Login mode.")
                                finally:
                                    db.close()
                            else:
                                st.error("Please fill all required fields.")
                                
                elif auth_mode == "Forgot Password":
                    with st.form("forgot_password"):
                        st.markdown("### Reset Password")
                        reset_username = st.text_input("Enter your Username")
                        new_pass = st.text_input("Enter New Password", type="password")
                        submit_reset = st.form_submit_button("Reset Password", type="primary", use_container_width=True)
                        
                        if submit_reset:
                            if reset_username and new_pass:
                                db = SessionLocal()
                                try:
                                    user = db.query(UserDB).filter(UserDB.username == reset_username).first()
                                    if user:
                                        user.password_hash = hash_password(new_pass)
                                        db.commit()
                                        st.success("Password reset successfully! Please switch to Login mode.")
                                        log_audit_event(user.id, "PASSWORD_RESET", "System", "User reset password")
                                    else:
                                        st.error("Username not found.")
                                finally:
                                    db.close()
                            else:
                                st.error("Please fill all required fields.")
        return False
    return True

def render_patient_portal():
    st.markdown(f"## Welcome, {st.session_state.user_name}")
    st.info("Here you can securely download your approved test reports.")
    
    tab_reports, tab_chat = st.tabs(["My Reports", "💬 Patient Support AI"])
    
    with tab_reports:
        db = SessionLocal()
        try:
            patient = db.query(PatientDB).filter(PatientDB.uhid == st.session_state.uhid).first()
            reports = db.query(ReportDB).filter(ReportDB.patient_id == patient.id, ReportDB.status == "Approved").order_by(ReportDB.created_at.desc()).all()
            
            if not reports:
                st.warning("You have no approved reports available for download at this time.")
            else:
                for rep in reports:
                    with st.container():
                        st.markdown(f"#### Report: {rep.test_type} | Date: {rep.created_at.strftime('%Y-%m-%d %H:%M')}")
                        
                        results = db.query(TestResultDB).filter(TestResultDB.report_id == rep.id).all()
                        res_data = [{"Investigation": r.investigation, "Result": r.value, "Unit": r.unit, "Reference Value": r.reference_range, "Status": r.status} for r in results]
                        df_res = pd.DataFrame(res_data)
                        interpretations = generate_interpretation(df_res, rep.test_type)
                        
                        pat_data = {
                            "name": patient.name,
                            "age": patient.age,
                            "gender": patient.gender,
                            "uhid": patient.uhid,
                            "ref_doc": rep.ref_doctor,
                            "sample_loc": rep.sample_loc,
                            "collection_time": rep.collection_time,
                            "report_time": rep.report_time
                        }
                        
                        pdf_bytes = bytes(create_pdf(pat_data, rep.test_type, res_data, interpretations))
                        
                        col1, col2, col3 = st.columns([6, 2, 2])
                        with col2:
                            view_btn = st.button("🖨️ Print / View", key=f"view_pat_{rep.id}")
                        with col3:
                            st.download_button("📄 Download PDF", data=pdf_bytes, file_name=f"{patient.uhid}_{rep.test_type}.pdf", mime="application/pdf", key=f"dl_pat_{rep.id}")
                            
                        if view_btn:
                            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600px" type="application/pdf" style="border: 1px solid #ccc; border-radius: 5px;"></iframe>'
                            st.markdown(pdf_display, unsafe_allow_html=True)
                        
                        inv = db.query(InvoiceDB).filter(InvoiceDB.report_id == rep.id).first()
                        if inv:
                            if inv.status == "Paid":
                                st.success("Payment Status: PAID")
                            else:
                                st.error(f"Payment Status: {inv.status} | Balance Due: ₹{inv.total_amount - inv.discount - inv.paid_amount}")
                        st.markdown("---")
        finally:
            db.close()
            
    with tab_chat:
        st.markdown("### 💬 Automated Patient Support")
        st.info("I can help answer questions about report timing, test preparation, and lab policies. For medical diagnoses, please consult your doctor.")
        
        if "patient_chat_history" not in st.session_state:
            st.session_state.patient_chat_history = []
            
        for msg in st.session_state.patient_chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
        if prompt := st.chat_input("Ask a question about your reports..."):
            st.session_state.patient_chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.spinner("AI is thinking..."):
                db = SessionLocal()
                try:
                    patient = db.query(PatientDB).filter(PatientDB.uhid == st.session_state.uhid).first()
                    pending = db.query(ReportDB).filter(ReportDB.patient_id == patient.id, ReportDB.status != "Approved").count() > 0
                finally:
                    db.close()
                    
                response = chat_with_patient_bot(prompt, patient.name, pending)
                st.session_state.patient_chat_history.append({"role": "assistant", "content": response})
                with st.chat_message("assistant"):
                    st.markdown(response)

def render_patient_dashboard():
    st.markdown("<div class='section-title'>👥 Patient Dashboard / MPI</div>", unsafe_allow_html=True)
    
    db = SessionLocal()
    try:
        search_term = st.text_input("Search Patients by Name or UHID", placeholder="Enter name or UHID...")
        
        query = db.query(PatientDB)
        if search_term:
            query = query.filter(
                (PatientDB.name.ilike(f"%{search_term}%")) | 
                (PatientDB.uhid.ilike(f"%{search_term}%"))
            )
            
        patients = query.all()
        
        if not patients:
            st.info("No patients found in the database.")
            return

        patient_data = [{
            "Database ID": p.id,
            "UHID": p.uhid,
            "Name": p.name,
            "Age": p.age,
            "Gender": p.gender,
            "Registered": p.created_at.strftime("%Y-%m-%d")
        } for p in patients]
        
        st.dataframe(pd.DataFrame(patient_data), use_container_width=True, hide_index=True)
        
        st.markdown("### View Patient History")
        selected_uhid = st.selectbox("Select Patient to view past reports", [p.uhid for p in patients])
        
        if selected_uhid:
            patient = db.query(PatientDB).filter(PatientDB.uhid == selected_uhid).first()
            reports = db.query(ReportDB).filter(ReportDB.patient_id == patient.id).order_by(ReportDB.created_at.desc()).all()
            
            if not reports:
                st.info("This patient has no recorded test reports.")
            else:
                for rep in reports:
                    status_color = "green" if rep.status == "Approved" else "orange"
                    with st.expander(f"Report: {rep.test_type} | Date: {rep.created_at.strftime('%Y-%m-%d %H:%M')} | Status: {rep.status}"):
                        st.write(f"**Referred By:** {rep.ref_doctor}")
                        
                        res_data = []
                        results = db.query(TestResultDB).filter(TestResultDB.report_id == rep.id).all()
                        for r in results:
                            res_data.append({
                                "Investigation": r.investigation,
                                "Result": r.value,
                                "Unit": r.unit,
                                "Reference Value": r.reference_range,
                                "Status": r.status
                            })
                            
                        df_res = pd.DataFrame(res_data)
                        styled_res = df_res.style.applymap(color_status, subset=['Status'])
                        st.dataframe(styled_res, use_container_width=True, hide_index=True)
                        
                        if rep.status == "Approved":
                            st.success("This report is Approved.")
                            
                            # Add Print/Download for staff
                            pat_data = {
                                "name": patient.name,
                                "age": patient.age,
                                "gender": patient.gender,
                                "uhid": patient.uhid,
                                "ref_doc": rep.ref_doctor,
                                "sample_loc": rep.sample_loc,
                                "collection_time": rep.collection_time,
                                "report_time": rep.report_time
                            }
                            interpretations = generate_interpretation(df_res, rep.test_type)
                            pdf_bytes = bytes(create_pdf(pat_data, rep.test_type, res_data, interpretations))
                            
                            c1, c2, c3 = st.columns([6, 2, 2])
                            with c2:
                                s_view_btn = st.button("🖨️ Print Report", key=f"view_staff_{rep.id}")
                            with c3:
                                st.download_button("📄 Download", data=pdf_bytes, file_name=f"{patient.uhid}_{rep.test_type}.pdf", mime="application/pdf", key=f"dl_staff_{rep.id}")
                                
                            if s_view_btn:
                                base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600px" type="application/pdf" style="border: 1px solid #ccc; border-radius: 5px;"></iframe>'
                                st.markdown(pdf_display, unsafe_allow_html=True)
                        else:
                            st.warning("This report is pending Pathologist approval.")
                            
            # Add Trend Analysis
            st.markdown("---")
            st.markdown("### 📈 Biomarker Trend History")
            
            if not reports:
                st.info("No historical reports found for this patient.")
            else:
                all_results = db.query(TestResultDB).join(ReportDB).filter(
                    ReportDB.patient_id == patient.id
                ).order_by(ReportDB.created_at.asc()).all()
                
                if all_results:
                    trend_data = {}
                    for r in all_results:
                        inv = r.investigation
                        date_str = r.report.created_at.strftime("%Y-%m-%d %H:%M")
                        status_label = " (Pending)" if r.report.status != "Approved" else ""
                        if inv not in trend_data:
                            trend_data[inv] = []
                        trend_data[inv].append({"Date": date_str + status_label, "Value": r.value})
                        
                    # Only show trend if patient has taken the test more than once
                    trend_tests = {k: v for k, v in trend_data.items() if len(v) > 1}
                    
                    if trend_tests:
                        st.info("The following markers have multiple data points over time:")
                        selected_trend = st.selectbox("Select Marker to View Trend", list(trend_tests.keys()))
                        if selected_trend:
                            df_trend = pd.DataFrame(trend_tests[selected_trend])
                            df_trend.set_index("Date", inplace=True)
                            st.line_chart(df_trend)
                    else:
                        st.info("To plot trend graphs, a patient needs multiple reports containing the exact same test parameter. Not enough data points yet.")

    finally:
        db.close()

def render_approval_workflow():
    st.markdown("<div class='section-title'>✅ Pathologist Approval Workflow</div>", unsafe_allow_html=True)
    db = SessionLocal()
    try:
        pending_reports = db.query(ReportDB).filter(ReportDB.status == "Result Entered").order_by(ReportDB.created_at.asc()).all()
        
        if not pending_reports:
            st.info("No reports pending approval.")
            return
            
        for rep in pending_reports:
            patient = rep.patient
            with st.expander(f"Pending: {patient.name} ({patient.uhid}) - {rep.test_type}"):
                st.write(f"**Collected:** {rep.collection_time}")
                
                res_data = []
                results = db.query(TestResultDB).filter(TestResultDB.report_id == rep.id).all()
                for r in results:
                    res_data.append({
                        "Investigation": r.investigation,
                        "Result": r.value,
                        "Unit": r.unit,
                        "Reference Value": r.reference_range,
                        "Status": r.status
                    })
                
                df_res = pd.DataFrame(res_data)
                styled_res = df_res.style.applymap(color_status, subset=['Status'])
                st.dataframe(styled_res, use_container_width=True, hide_index=True)
                
                # Fetch AI Job for Human-in-the-Loop review
                ai_job = db.query(AIJobDB).filter(AIJobDB.target_entity_id == rep.id, AIJobDB.job_type == "REPORT_DRAFT").first()
                if ai_job and ai_job.output_payload:
                    try:
                        ai_data = json.loads(ai_job.output_payload)
                        st.markdown("#### 🤖 AI Drafting Assistant Review")
                        if ai_data.get("needs_manual_review"):
                            st.warning("⚠️ AI Flagged for Review: " + ", ".join(ai_data.get("review_reasons", [])))
                        
                        edited_summary = st.text_area("Clinical Summary (Edit as needed)", value=ai_data.get("report_summary", ""), key=f"summary_{rep.id}")
                        edited_patient_friendly = st.text_area("Patient-Friendly Summary", value=ai_data.get("patient_friendly_summary", ""), key=f"pat_summary_{rep.id}")
                    except Exception as e:
                        st.error("Failed to load AI draft.")
                
                if st.button(f"Approve & Finalize Report #{rep.id}", key=f"approve_{rep.id}", type="primary"):
                    rep.status = "Approved"
                    rep.approved_by_id = st.session_state.user_id
                    
                    if ai_job:
                        ai_job.human_approved = True
                        ai_job.status = "COMPLETED"
                        # Ensure the final edits are saved back
                        try:
                            ai_data["report_summary"] = edited_summary
                            ai_data["patient_friendly_summary"] = edited_patient_friendly
                            ai_job.output_payload = json.dumps(ai_data)
                        except:
                            pass
                            
                    db.commit()
                    log_audit_event(st.session_state.user_id, "APPROVE", "Report", f"Approved report #{rep.id}")
                    st.success("Report approved successfully!")
                    st.rerun()
    finally:
        db.close()

def render_billing_dashboard():
    st.markdown("<div class='section-title'>💰 Billing & Invoices</div>", unsafe_allow_html=True)
    db = SessionLocal()
    try:
        invoices = db.query(InvoiceDB).order_by(InvoiceDB.created_at.desc()).all()
        if not invoices:
            st.info("No invoices found.")
            return
            
        inv_data = []
        for inv in invoices:
            patient = db.query(PatientDB).filter(PatientDB.id == inv.patient_id).first()
            report = db.query(ReportDB).filter(ReportDB.id == inv.report_id).first()
            inv_data.append({
                "Inv ID": f"INV-{inv.id}",
                "Date": inv.created_at.strftime("%Y-%m-%d"),
                "Patient": patient.name,
                "Test": report.test_type,
                "Total": inv.total_amount,
                "Discount": inv.discount,
                "Paid": inv.paid_amount,
                "Due": inv.total_amount - inv.discount - inv.paid_amount,
                "Status": inv.status
            })
        st.dataframe(pd.DataFrame(inv_data), use_container_width=True, hide_index=True)
    finally:
        db.close()

def render_analytics_dashboard():
    st.markdown("<div class='section-title'>📈 Analytics & Insights</div>", unsafe_allow_html=True)
    db = SessionLocal()
    try:
        total_patients = db.query(PatientDB).count()
        total_reports = db.query(ReportDB).count()
        pending_reports = db.query(ReportDB).filter(ReportDB.status == "Result Entered").count()
        
        invoices = db.query(InvoiceDB).all()
        total_revenue = sum([inv.total_amount - inv.discount for inv in invoices])
        collected_revenue = sum([inv.paid_amount for inv in invoices])
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Patients", total_patients)
        col2.metric("Total Reports", total_reports)
        col3.metric("Pending Approvals", pending_reports)
        col4.metric("Collected Revenue", f"₹{collected_revenue:,.0f}")
        
        st.markdown("---")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Report Status Distribution**")
            status_counts = db.query(ReportDB.status).all()
            if status_counts:
                df_status = pd.DataFrame(status_counts, columns=["Status"])
                status_agg = df_status["Status"].value_counts().reset_index()
                status_agg.columns = ["Status", "Count"]
                st.bar_chart(status_agg.set_index("Status"))
            else:
                st.info("No reports generated yet.")
                
        with c2:
            st.markdown("**Revenue Collection Overview**")
            if invoices:
                rev_data = pd.DataFrame([
                    {"Category": "Collected", "Amount": collected_revenue},
                    {"Category": "Pending Dues", "Amount": total_revenue - collected_revenue}
                ])
                st.bar_chart(rev_data.set_index("Category"))
            else:
                st.info("No revenue generated yet.")
                
        st.markdown("---")
        st.markdown("### 🤖 Analytics Copilot Insights")
        with st.spinner("Analyzing operational data..."):
            metrics = {
                'total_revenue': total_revenue,
                'total_reports': total_reports
            }
            insights = generate_analytics_insights(metrics)
            for ins in insights:
                st.info(f"💡 {ins}")
                
    finally:
        db.close()

def render_triage_alerts():
    st.markdown("<div class='section-title'>🚨 Smart Triage & Alert Center</div>", unsafe_allow_html=True)
    st.info("AI heuristics continuously scan pending workloads to flag urgent cases or data anomalies.")
    
    db = SessionLocal()
    try:
        pending = db.query(ReportDB).filter(ReportDB.status == "Result Entered").all()
        if not pending:
            st.success("No pending reports in the queue. All clear!")
            return
            
        pending_data = []
        for rep in pending:
            results = db.query(TestResultDB).filter(TestResultDB.report_id == rep.id).all()
            res_statuses = [res.status for res in results]
            
            p_data = {"id": rep.id, "test_type": rep.test_type}
            
            if any("Critical" in str(status) for status in res_statuses):
                p_data["has_critical"] = True
                
            pending_data.append(p_data)
            
        alerts = generate_smart_triage_alerts(pending_data)
        
        for alert in alerts:
            if alert['level'] == 'CRITICAL':
                st.error(f"🚨 **CRITICAL**: {alert['message']}")
            elif alert['level'] == 'WARNING':
                st.warning(f"⚠️ **WARNING**: {alert['message']}")
            else:
                st.info(f"ℹ️ **INFO**: {alert['message']}")
    finally:
        db.close()

def render_test_catalog():
    st.markdown("<div class='section-title'>⚙️ Test Catalog Management</div>", unsafe_allow_html=True)
    st.info("Edit reference ranges and parameters directly in the table below.")
    
    test_options = get_test_options()
    if not test_options:
        st.warning("No tests configured.")
        return
        
    selected_test = st.selectbox("Select Test Panel to Edit", test_options)
    
    db = SessionLocal()
    try:
        test = db.query(TestConfigDB).filter(TestConfigDB.name == selected_test).first()
        
        # Edit Base Test Price
        new_price = st.number_input("Test Price (₹)", value=test.price, step=50.0)
        if new_price != test.price:
            if st.button("Update Price"):
                test.price = new_price
                db.commit()
                st.success("Price updated.")
        
        params = db.query(TestParameterDB).filter(TestParameterDB.test_config_id == test.id).all()
        param_data = [{
            "Investigation": p.investigation,
            "Ref_Min": p.ref_min,
            "Ref_Max": p.ref_max,
            "Unit": p.unit
        } for p in params]
        
        df = pd.DataFrame(param_data)
        
        edited_df = st.data_editor(
            df,
            column_config={
                "Investigation": st.column_config.TextColumn("Investigation", disabled=False),
                "Ref_Min": st.column_config.NumberColumn("Min Reference", format="%.1f"),
                "Ref_Max": st.column_config.NumberColumn("Max Reference", format="%.1f"),
                "Unit": st.column_config.TextColumn("Unit")
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic"
        )
        
        if st.button("Save Changes to Database", type="primary"):
            db.query(TestParameterDB).filter(TestParameterDB.test_config_id == test.id).delete()
            for _, row in edited_df.iterrows():
                if pd.notna(row['Investigation']) and str(row['Investigation']).strip() != "":
                    new_param = TestParameterDB(
                        test_config_id=test.id,
                        investigation=str(row['Investigation']).strip(),
                        ref_min=float(row['Ref_Min']) if pd.notna(row['Ref_Min']) else 0.0,
                        ref_max=float(row['Ref_Max']) if pd.notna(row['Ref_Max']) else 0.0,
                        unit=str(row['Unit']).strip() if pd.notna(row['Unit']) else ""
                    )
                    db.add(new_param)
            db.commit()
            log_audit_event(st.session_state.user_id, "UPDATE", "TestCatalog", f"Updated {selected_test} parameters")
            st.success(f"Successfully updated configuration for {selected_test}!")
    finally:
        db.close()

def render_new_report():
    init_session_state()
    
    logo_b64 = get_base64_of_bin_file("logo.png")
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="90" style="border-radius: 8px;">' if logo_b64 else '<div class="placeholder-box" style="padding: 15px 25px;">LOGO<br>PLACEHOLDER</div>'
    
    qr_b64 = generate_qr_base64(st.session_state.patient_data.get("uhid", "UNKNOWN"))
    qr_html = f'<img src="data:image/png;base64,{qr_b64}" width="90" style="border-radius: 8px;">'
    
    st.markdown(f"""
    <div class="report-header">
        <div>
            {logo_html}
        </div>
        <div style="text-align: center;">
            <p class="lab-title">Dr. Bimala Mishra Pathology</p>
            <p class="lab-tagline">MBBS, MD, Pathology Specialist</p>
            <p class="lab-contact">
                📍 Matashai, New Bustand, Bhadrak, 756100<br>
                📞 +91 9876543210 | ✉️ info@bimalapathology.com
            </p>
        </div>
        <div>
            {qr_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='section-card'><div class='section-title'>Patient Information</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.session_state.patient_data["name"] = st.text_input("Patient Name", st.session_state.patient_data["name"])
        st.session_state.patient_data["uhid"] = st.text_input("Patient ID / UHID", st.session_state.patient_data["uhid"])
    with col2:
        st.session_state.patient_data["age"] = st.number_input("Age", min_value=0, max_value=120, value=st.session_state.patient_data["age"])
        gender_options = ["Male", "Female", "Other"]
        default_index = gender_options.index(st.session_state.patient_data["gender"]) if st.session_state.patient_data["gender"] in gender_options else 0
        st.session_state.patient_data["gender"] = st.selectbox("Gender", gender_options, index=default_index)
    with col3:
        st.session_state.patient_data["ref_doc"] = st.text_input("Ref. By Doctor", st.session_state.patient_data["ref_doc"])
        st.session_state.patient_data["sample_loc"] = st.text_input("Sample Collected At", st.session_state.patient_data["sample_loc"])
    with col4:
        st.session_state.patient_data["collection_time"] = st.text_input("Collection Time", st.session_state.patient_data["collection_time"])
        st.session_state.patient_data["report_time"] = st.text_input("Report Time", st.session_state.patient_data["report_time"])
        
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-card'><div class='section-title'>Test Configuration & Billing</div>", unsafe_allow_html=True)
    test_options = get_test_options()
    
    if not test_options:
        st.warning("No tests configured in the database.")
        return
        
    selected_tests = st.multiselect("Select Test Panels", test_options, default=st.session_state.get("selected_tests", [test_options[0]] if test_options else []))
    
    if selected_tests != st.session_state.get("selected_tests", []):
        st.session_state.selected_tests = selected_tests
        st.session_state.test_results = {}
        st.session_state.report_generated = False
        st.rerun()
        
    if not selected_tests:
        st.warning("Please select at least one test panel to proceed.")
        return
        
    test_price = sum([get_test_price(t) for t in selected_tests])
    test_type_str = ", ".join(selected_tests)
    
    bcol1, bcol2, bcol3, bcol4 = st.columns(4)
    with bcol1:
        st.markdown(f"**Total Price:** ₹{test_price}")
    with bcol2:
        discount = st.number_input("Discount (₹)", min_value=0.0, value=0.0, step=50.0)
    with bcol3:
        paid = st.number_input("Paid Amount (₹)", min_value=0.0, value=(test_price - discount), step=50.0)
    with bcol4:
        pay_mode = st.selectbox("Payment Mode", ["Cash", "UPI", "Card"])
        
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown(f"<div class='section-card'><div class='section-title'>Input Test Values: {test_type_str}</div>", unsafe_allow_html=True)
    
    test_params = []
    for t in selected_tests:
        test_params.extend(get_test_params(t))
        
    if not test_params:
        st.warning("No parameters configured for the selected tests.")
        return
        
    with st.form("test_input_form"):
        h_col1, h_col2, h_col3 = st.columns([2, 1, 1])
        h_col1.markdown("**Investigation**")
        h_col2.markdown("**Result Input**")
        h_col3.markdown("**Reference & Unit**")
        st.markdown("---")
        
        current_inputs = {}
        for param in test_params:
            i_col1, i_col2, i_col3 = st.columns([2, 1, 1])
            i_col1.markdown(f"<div style='padding-top: 8px;'>{param['Investigation']}</div>", unsafe_allow_html=True)
            
            with i_col2:
                if param['Investigation'] in st.session_state.test_results:
                    default_val = st.session_state.test_results[param['Investigation']]
                else:
                    default_val = round((param['Ref_Min'] + param['Ref_Max']) / 2, 1)
                    
                res = st.number_input(f"Result for {param['Investigation']}", value=default_val, step=0.1, label_visibility="collapsed")
                current_inputs[param['Investigation']] = res
                
            with i_col3:
                st.markdown(f"<div style='padding-top: 8px; color: #666; font-size: 14px;'>{param['Ref_Min']} - {param['Ref_Max']} {param['Unit']}</div>", unsafe_allow_html=True)
                
        submit_report = st.form_submit_button("Submit Draft Report & Generate Invoice", type="primary", use_container_width=True)
        
    st.markdown("</div>", unsafe_allow_html=True)

    if submit_report:
        try:
            valid_patient = PatientSchema(**st.session_state.patient_data)
        except ValidationError as e:
            st.error("Validation Error in Patient Information:")
            for err in e.errors():
                st.error(f"- {err['loc'][0]}: {err['msg']}")
            return

        st.session_state.test_results = current_inputs
        
        report_data = []
        for param in test_params:
            val = st.session_state.test_results.get(param['Investigation'], 0.0)
            status = evaluate_result(val, param['Ref_Min'], param['Ref_Max'])
            ref_str = f"{param['Ref_Min']} - {param['Ref_Max']}" if param['Ref_Min'] != 0.0 else f"< {param['Ref_Max']}"
            report_data.append({
                "Investigation": param['Investigation'],
                "Result": f"{val:.1f}",
                "Reference Value": ref_str,
                "Unit": param['Unit'],
                "Status": status
            })

        if save_to_database(valid_patient, test_type_str, report_data, st.session_state.user_id, test_price, discount, paid, pay_mode):
            st.success("Report and Invoice generated! The report is pending Pathologist approval.")
            st.session_state.report_generated = True
            st.session_state.report_data_cache = report_data

    # Display Preview
    if st.session_state.report_generated:
        st.markdown("---")
        st.info("This is a preview of the drafted report.")
        
        df_report = pd.DataFrame(st.session_state.report_data_cache)
        interpretations = generate_interpretation(df_report, test_type_str)
        
        pdf_bytes = bytes(create_pdf(
            st.session_state.patient_data, 
            test_type_str, 
            st.session_state.report_data_cache, 
            interpretations
        ))
        
        col_title, col_btn = st.columns([8, 2])
        with col_title:
            st.markdown(f"<h2 style='color: #0056b3; margin-bottom: 20px;'>Report Preview: {test_type_str}</h2>", unsafe_allow_html=True)
        with col_btn:
            st.download_button(
                label="📄 Download Draft PDF",
                data=pdf_bytes,
                file_name=f"{st.session_state.patient_data['uhid']}_DRAFT.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        
        styled_df = df_report.style.applymap(color_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

def render_idp_module():
    st.markdown("<div class='section-title'>📄 Intelligent Document Processing (OCR)</div>", unsafe_allow_html=True)
    st.info("Upload scanned prescriptions or legacy lab reports to automatically extract data using AI.")
    
    uploaded_file = st.file_uploader("Upload Document (PDF, PNG, JPG)", type=["pdf", "png", "jpg"])
    doc_type = st.selectbox("Document Type", ["PRESCRIPTION", "LEGACY_REPORT"])
    
    if uploaded_file and st.button("Process Document with AI", type="primary"):
        # File Validation: Max 5MB limit
        if uploaded_file.size > 5 * 1024 * 1024:
            st.error("File size exceeds the 5MB maximum limit. Please upload a smaller file.")
        else:
            with st.spinner("Extracting data via OCR & LLM..."):
                # Sanitize filename to prevent path traversal
                safe_name = "".join(c for c in uploaded_file.name if c.isalnum() or c in "._- ")
                file_path = f"temp_{safe_name}"
                
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                    
                ai_output = extract_data_from_document(file_path, doc_type)
            
            db = SessionLocal()
            try:
                new_doc = DocumentDB(
                    file_path=file_path,
                    doc_type=doc_type,
                    extracted_data=ai_output
                )
                db.add(new_doc)
                db.commit()
                st.success("Document processed successfully!")
                st.session_state.last_processed_doc = new_doc.id
            except Exception as e:
                db.rollback()
                st.error("Database Error")
            finally:
                db.close()
                
    if "last_processed_doc" in st.session_state:
        db = SessionLocal()
        try:
            doc = db.query(DocumentDB).filter(DocumentDB.id == st.session_state.last_processed_doc).first()
            if doc:
                st.markdown("### 🔍 Verification & Correction")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Uploaded File Preview**")
                    if doc.file_path.lower().endswith((".png", ".jpg", ".jpeg")):
                        st.image(doc.file_path, use_container_width=True)
                    else:
                        st.info(f"File stored at: {doc.file_path} (Preview unavailable for this format)")
                
                with c2:
                    st.markdown("**AI Extracted Data**")
                    data = json.loads(doc.extracted_data)
                    st.json(data)
                    
                    st.markdown("**Manual Overrides**")
                    edited_patient = st.text_input("Patient Name", value=data.get("patient_name", ""))
                    edited_doctor = st.text_input("Referring Doctor", value=data.get("referring_doctor", ""))
                    
                    if st.button("Verify & Save to Records", type="primary"):
                        doc.verified = True
                        data["patient_name"] = edited_patient
                        data["referring_doctor"] = edited_doctor
                        doc.extracted_data = json.dumps(data)
                        db.commit()
                        st.success("Data verified and synced to LIS!")
                        del st.session_state.last_processed_doc
                        st.rerun()
        finally:
            db.close()

def render_staff_rag():
    st.markdown("<div class='section-title'>📚 Staff Knowledge Assistant</div>", unsafe_allow_html=True)
    st.info("Query the internal SOPs, pricing catalogs, and lab policies using AI Vector Search.")
    
    if "staff_chat_history" not in st.session_state:
        st.session_state.staff_chat_history = []
        
    for msg in st.session_state.staff_chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("Ask about lab policies, pricing, or sample handling..."):
        st.session_state.staff_chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.spinner("Searching Vector Database..."):
            response = chat_with_staff_rag(prompt)
            st.session_state.staff_chat_history.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)

def main():
    if not check_auth():
        return
        
    st.sidebar.markdown(f"### 👤 {st.session_state.user_name}")
    st.sidebar.markdown(f"**Role:** {st.session_state.user_role}")
    st.sidebar.markdown("---")
    
    if st.session_state.user_role == "Patient":
        render_patient_portal()
    else:
        # Determine accessible modules based on role
        modules = ["👥 Patient Dashboard / MPI"]
        
        if st.session_state.user_role in ["Admin", "Technician", "Receptionist"]:
            modules.insert(0, "📝 New Report Entry")
            
        if st.session_state.user_role in ["Admin", "Receptionist", "Pathologist"]:
            modules.append("💰 Billing & Invoices")
            
        if st.session_state.user_role in ["Admin", "Pathologist"]:
            modules.append("🚨 Smart Triage & Alerts")
            modules.append("✅ Approval Workflow")
            
        if st.session_state.user_role in ["Admin", "Receptionist", "Technician", "Pathologist"]:
            modules.append("📄 Intelligent Document Processing")
            modules.append("📚 Staff Knowledge Assistant")
            
        if st.session_state.user_role in ["Admin", "Manager"]:
            modules.append("📈 Analytics & Insights")
            
        if st.session_state.user_role == "Admin":
            modules.append("⚙️ Test Catalog")
            
        menu_selection = st.sidebar.radio("Select Module", modules)
        
        st.sidebar.markdown("---")
        if st.sidebar.button("Logout"):
            if st.session_state.user_role != "Patient":
                log_audit_event(st.session_state.user_id, "LOGOUT", "System", "User logged out")
            st.session_state.authenticated = False
            st.rerun()
            
        if menu_selection == "📝 New Report Entry":
            render_new_report()
        elif menu_selection == "👥 Patient Dashboard / MPI":
            render_patient_dashboard()
        elif menu_selection == "🚨 Smart Triage & Alerts":
            render_triage_alerts()
        elif menu_selection == "✅ Approval Workflow":
            render_approval_workflow()
        elif menu_selection == "⚙️ Test Catalog":
            render_test_catalog()
        elif menu_selection == "📄 Intelligent Document Processing":
            render_idp_module()
        elif menu_selection == "📚 Staff Knowledge Assistant":
            render_staff_rag()
        elif menu_selection == "💰 Billing & Invoices":
            render_billing_dashboard()
        elif menu_selection == "📈 Analytics & Insights":
            render_analytics_dashboard()

if __name__ == "__main__":
    main()
