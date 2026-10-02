import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "sample_documents")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_gst_pdf():
    file_path = os.path.join(OUTPUT_DIR, "Sample_GST_Certificate.pdf")
    doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('T1', fontName='Helvetica-Bold', fontSize=14, alignment=1, textColor=colors.HexColor('#0F172A'))
    sub_style = ParagraphStyle('T2', fontName='Helvetica', fontSize=10, alignment=1, textColor=colors.HexColor('#475569'))
    body_style = ParagraphStyle('B1', fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#1E293B'))
    bold_style = ParagraphStyle('B2', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#0F172A'))

    story = [
        Paragraph("<b>GOVERNMENT OF INDIA</b>", title_style),
        Paragraph("FORM GST REG-06", sub_style),
        Paragraph("<b>REGISTRATION CERTIFICATE</b>", title_style),
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0F172A')),
        Spacer(1, 10)
    ]

    data = [
        [Paragraph("<b>Registration Number (GSTIN):</b>", bold_style), Paragraph("<b>36ABCDE1234F1Z5</b>", bold_style)],
        [Paragraph("<b>Legal Name:</b>", bold_style), Paragraph("Alpha Logix Solutions Private Limited", body_style)],
        [Paragraph("<b>Trade Name:</b>", bold_style), Paragraph("Alpha Logix Tech", body_style)],
        [Paragraph("<b>Constitution of Business:</b>", bold_style), Paragraph("Private Limited Company", body_style)],
        [Paragraph("<b>Address of Principal Place of Business:</b>", bold_style), Paragraph("Plot 42, Hitech City, Madhapur, Hyderabad, Telangana - 500081", body_style)],
        [Paragraph("<b>Date of Liability:</b>", bold_style), Paragraph("15/04/2020", body_style)],
        [Paragraph("<b>Period of Validity:</b>", bold_style), Paragraph("From: 15/04/2020 To: Regular", body_style)],
        [Paragraph("<b>Type of Registration:</b>", bold_style), Paragraph("Regular Taxpayer", body_style)],
    ]
    t = Table(data, colWidths=[200, 320])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F8FAFC')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    doc.build(story)
    print("Generated:", file_path)

def generate_pan_image():
    file_path = os.path.join(OUTPUT_DIR, "Sample_PAN_Card.png")
    width, height = 700, 420
    img = Image.new('RGB', (width, height), color=(240, 245, 255))
    draw = ImageDraw.Draw(img)

    # Outer border and header bar
    draw.rectangle([(10, 10), (width - 10, height - 10)], outline=(30, 64, 175), width=3)
    draw.rectangle([(12, 12), (width - 12, 70)], fill=(30, 64, 175))

    draw.text((180, 25), "INCOME TAX DEPARTMENT", fill=(255, 255, 255))
    draw.text((220, 45), "GOVT. OF INDIA", fill=(220, 235, 255))

    # Body Details
    draw.text((50, 100), "Permanent Account Number (PAN):", fill=(70, 70, 70))
    draw.text((50, 125), "ABCDE1234F", fill=(10, 10, 10))

    draw.text((50, 170), "Name of Entity / Cardholder:", fill=(70, 70, 70))
    draw.text((50, 195), "ALPHA LOGIX SOLUTIONS PRIVATE LIMITED", fill=(10, 10, 10))

    draw.text((50, 240), "Father's / Director's Name:", fill=(70, 70, 70))
    draw.text((50, 265), "RAJESH SHARMA (DIRECTOR)", fill=(10, 10, 10))

    draw.text((50, 310), "Date of Incorporation:", fill=(70, 70, 70))
    draw.text((50, 335), "15/04/2020", fill=(10, 10, 10))

    # Simulated Hologram / QR box
    draw.rectangle([(width - 160, 120), (width - 40, 240)], outline=(100, 100, 100), fill=(220, 220, 220), width=1)
    draw.text((width - 145, 170), "[ OFFICIAL ]", fill=(80, 80, 80))

    img.save(file_path)
    print("Generated:", file_path)

def generate_udyam_pdf():
    file_path = os.path.join(OUTPUT_DIR, "Sample_Udyam_Certificate.pdf")
    doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('T1', fontName='Helvetica-Bold', fontSize=14, alignment=1, textColor=colors.HexColor('#0F172A'))
    sub_style = ParagraphStyle('T2', fontName='Helvetica', fontSize=10, alignment=1, textColor=colors.HexColor('#475569'))
    body_style = ParagraphStyle('B1', fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#1E293B'))
    bold_style = ParagraphStyle('B2', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#0F172A'))

    story = [
        Paragraph("<b>MINISTRY OF MICRO, SMALL & MEDIUM ENTERPRISES</b>", title_style),
        Paragraph("UDYAM REGISTRATION CERTIFICATE", sub_style),
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0F172A')),
        Spacer(1, 10)
    ]

    data = [
        [Paragraph("<b>Udyam Registration Number:</b>", bold_style), Paragraph("<b>UDYAM-TS-02-0012345</b>", bold_style)],
        [Paragraph("<b>Name of Enterprise:</b>", bold_style), Paragraph("Alpha Logix Solutions Private Limited", body_style)],
        [Paragraph("<b>Type of Enterprise:</b>", bold_style), Paragraph("Medium Enterprise", body_style)],
        [Paragraph("<b>Major Activity:</b>", bold_style), Paragraph("Services (IT Consulting & Procurement)", body_style)],
        [Paragraph("<b>Social Category of Entrepreneur:</b>", bold_style), Paragraph("General", body_style)],
        [Paragraph("<b>Official Address of Enterprise:</b>", bold_style), Paragraph("Plot 42, Hitech City, Madhapur, Hyderabad, Telangana - 500081", body_style)],
        [Paragraph("<b>Date of Incorporation:</b>", bold_style), Paragraph("15/04/2020", body_style)],
        [Paragraph("<b>Date of Udyam Registration:</b>", bold_style), Paragraph("20/05/2020", body_style)],
    ]
    t = Table(data, colWidths=[200, 320])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F8FAFC')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    doc.build(story)
    print("Generated:", file_path)

if __name__ == "__main__":
    generate_gst_pdf()
    generate_pan_image()
    generate_udyam_pdf()
    print("All sample documents successfully generated!")
