from fpdf import FPDF
from datetime import datetime

class PathologyReportPDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 20)
        self.set_text_color(15, 118, 110) # Primary color
        self.cell(0, 10, "Dr. Bimala Mishra Pathology", ln=True, align="C")
        self.set_font("helvetica", "I", 10)
        self.set_text_color(20, 184, 166) # Accent
        self.cell(0, 5, "Reliable | Precise | Trusted", ln=True, align="C")
        self.set_font("helvetica", "", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "Matashai, New Bustand, Bhadrak, 756100 | +91 9876543210", ln=True, align="C")
        self.cell(0, 5, "MBBS, MD, Pathology Specialist", ln=True, align="C")
        self.line(10, 35, 200, 35)
        self.ln(10)

    def footer(self):
        self.set_y(-30)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128)
        
        self.set_y(-25)
        self.set_font("helvetica", "B", 10)
        self.cell(90, 6, "Medical Lab Technician", ln=False, align="L")
        self.cell(90, 6, "Dr. Bimala Mishra", ln=True, align="R")
        
        self.set_font("helvetica", "", 10)
        self.cell(90, 6, "Registration No: MLT-54321", ln=False, align="L")
        self.cell(90, 6, "MBBS, MD, Pathology Specialist", ln=True, align="R")
        
        self.cell(90, 6, "", ln=False, align="L")
        self.cell(90, 6, "Consultant Pathologist", ln=True, align="R")

def create_pdf(patient_data, selected_test, report_data, interpretations):
    pdf = PathologyReportPDF()
    pdf.add_page()
    
    # Patient Info Box
    pdf.set_fill_color(245, 251, 251)
    pdf.rect(10, 40, 190, 30, 'F')
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(0,0,0)
    
    pdf.set_xy(15, 42)
    pdf.cell(40, 6, f"Patient Name: {patient_data.get('name', '')}")
    pdf.set_xy(110, 42)
    pdf.cell(40, 6, f"Age/Gender: {patient_data.get('age', '')} / {patient_data.get('gender', '')}")
    
    pdf.set_xy(15, 48)
    pdf.cell(40, 6, f"UHID: {patient_data.get('uhid', '')}")
    pdf.set_xy(110, 48)
    pdf.cell(40, 6, f"Ref. Doctor: {patient_data.get('ref_doc', '')}")

    pdf.set_xy(15, 54)
    pdf.cell(40, 6, f"Collection: {patient_data.get('collection_time', '')}")
    pdf.set_xy(110, 54)
    pdf.cell(40, 6, f"Report: {patient_data.get('report_time', '')}")
    
    pdf.ln(15)
    
    # Title
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(15, 118, 110)
    pdf.cell(0, 10, f"Test: {selected_test}", ln=True, align="C")
    pdf.ln(5)
    
    # Table Header
    pdf.set_fill_color(15, 118, 110)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(60, 8, "Investigation", 1, 0, 'C', True)
    pdf.cell(30, 8, "Result", 1, 0, 'C', True)
    pdf.cell(30, 8, "Unit", 1, 0, 'C', True)
    pdf.cell(40, 8, "Reference", 1, 0, 'C', True)
    pdf.cell(30, 8, "Status", 1, 1, 'C', True)
    
    # Table Body
    pdf.set_text_color(0, 0, 0)
    for row in report_data:
        pdf.set_font("helvetica", "", 10)
        
        status = row["Status"]
        if "Critical" in status:
            pdf.set_text_color(139, 0, 0)
            pdf.set_font("helvetica", "B", 10)
        elif "High" in status:
            pdf.set_text_color(204, 0, 0)
            pdf.set_font("helvetica", "B", 10)
        elif "Low" in status:
            pdf.set_text_color(211, 84, 0)
            pdf.set_font("helvetica", "B", 10)
        else:
            pdf.set_text_color(0, 0, 0)
            
        pdf.cell(60, 8, row["Investigation"], 1, 0, 'L')
        pdf.cell(30, 8, str(row["Result"]), 1, 0, 'C')
        pdf.cell(30, 8, row["Unit"], 1, 0, 'C')
        pdf.cell(40, 8, row["Reference Value"], 1, 0, 'C')
        pdf.cell(30, 8, status, 1, 1, 'C')
        
    pdf.ln(10)
    
    # Interpretation
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Auto Interpretation Summary", ln=True)
    pdf.set_font("helvetica", "", 10)
    
    for text in interpretations:
        if "All parameters" in text:
            pdf.set_text_color(39, 174, 96)
        else:
            pdf.set_text_color(204, 0, 0)
        # Use simple string replacement for utf-8 chars if needed, fpdf2 handles unicode alright mostly but arrow can be tricky
        clean_text = text.replace("→", "->")
        pdf.set_x(10)
        pdf.multi_cell(190, 6, txt=f"* {clean_text}")
        
    out = pdf.output(dest="S")
    if isinstance(out, str):
        return out.encode("latin-1")
    return out
