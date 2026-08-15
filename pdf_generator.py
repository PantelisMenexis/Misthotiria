import datetime
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from classes.lease import Lease

def generate_lease_pdf(lease: Lease, file_path):
    """Παράγει την Καρτέλα Στοιχείων Μίσθωσης σε PDF υποστηρίζοντας πολλαπλά ακίνητα"""

    # 1. Φόρτωση Ελληνικής Γραμματοσειράς
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))

    # 2. Αρχικοποίηση Εγγράφου στην επιλεγμένη διαδρομή
    doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []

    # 3. Ορισμός Στυλ Κειμένου
    title_style = ParagraphStyle(
        'MainTitle', fontName='DejaVuSans', fontSize=15, leading=20, alignment=1, spaceAfter=15
    )
    section_style = ParagraphStyle(
        'SectionTitle', fontName='DejaVuSans', fontSize=11, leading=15, spaceBefore=10, spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyText', fontName='DejaVuSans', fontSize=10, leading=16, spaceAfter=4
    )

    # Μετατροπή ημερομηνιών σε ελληνική μορφή
    start_greek = lease.start.strftime("%d-%m-%Y") if isinstance(lease.start, datetime.date) else str(lease.start)
    end_greek = lease.end.strftime("%d-%m-%Y") if isinstance(lease.end, datetime.date) else str(lease.end)

    # --- ΣΥΝΘΕΣΗ PDF ---

    # Τίτλος Καρτέλας
    story.append(Paragraph(f"<b>📄 ΚΑΡΤΕΛΑ ΜΙΣΘΩΣΗΣ (ID: {lease.leaseId})</b>", title_style))
    story.append(HRFlowable(width="100%", thickness=1, color="#0078d4", spaceBefore=1, spaceAfter=10))

    # Ενότητα 1: Βασικά Στοιχεία
    story.append(Paragraph(f"• <b>Κατηγορία / Είδος Μίσθωσης:</b> {lease.leaseType}", body_style))
    story.append(Paragraph(f"• <b>Ημερομηνία Έναρξης:</b> {start_greek} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Ημερομηνία Λήξης:</b> {end_greek}", body_style))
    story.append(Paragraph(f"• <b>Συνολικό Μηνιαίο Ενοίκιο:</b> <font color='green'><b>{lease.amount:.2f} €</b></font>", body_style))

    story.append(HRFlowable(width="100%", thickness=0.5, color="#ccc", spaceBefore=8, spaceAfter=8))

    # Ενότητα 2: Συμβαλλόμενοι
    story.append(Paragraph("<b>👑 ΕΚΜΙΣΘΩΤΕΣ / ΙΔΙΟΚΤΗΤΕΣ</b>", section_style))
    for landlord in lease.landlords:
        story.append(Paragraph(f"• {landlord.firstName} {landlord.lastName} | ΑΦΜ: {landlord.afm} | Τηλ: {landlord.phone}", body_style))

    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>👤 ΜΙΣΘΩΤΕΣ / ΕΝΟΙΚΙΑΣΤΕΣ</b>", section_style))
    for tenant in lease.tenants:
        story.append(Paragraph(f"• {tenant.firstName} {tenant.lastName} | ΑΦΜ: {tenant.afm} | Τηλ: {tenant.phone}", body_style))

    story.append(HRFlowable(width="100%", thickness=0.5, color="#ccc", spaceBefore=8, spaceAfter=8))

    # Ενότητα 3: Στοιχεία Ακινήτων (Δυναμικό Loop για πολλαπλά ακίνητα)
    story.append(Paragraph("<b>🏠 ΣΤΟΙΧΕΙΑ ΑΚΙΝΗΤΩΝ</b>", section_style))

    is_multiple = len(lease.properties) > 1

    for idx, prop in enumerate(lease.properties):
        # Αν είναι πάνω από ένα ακίνητο, βάζουμε έναν ξεχωριστό υπότιτλο για το καθένα
        if is_multiple:
            story.append(Paragraph(f"<b>📍 Ακίνητο #{idx + 1} (Α/Α: {prop.aa} | Επιμέρους Μίσθωμα: {prop.sub_amount:.2f} €)</b>", body_style))

        dei_str = prop.deiNumber if prop.deiNumber else "Δεν ορίστηκε (Αγροτικό)"
        atak_str = prop.atak if prop.atak else "Δεν ορίστηκε"
        number_str = f" {prop.number}" if prop.number else "0"

        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;• <b>Διεύθυνση:</b> {prop.street}{number_str}, {prop.area} (ΤΚ: {prop.postalCode if prop.postalCode else '-'})", body_style))
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;• <b>Χαρακτηριστικά:</b> {prop.propertyType if prop.propertyType else '-'} | <b>Όροφος:</b> {prop.floor} | <b>Εμβαδόν:</b> {prop.squareMeters} τ.μ.", body_style))
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;• <b>Αριθμός Παροχής ΔΕΗ:</b> {dei_str} | <b>Αριθμός ΑΤΑΚ:</b> {atak_str}", body_style))

        if is_multiple and idx < len(lease.properties) - 1:
            story.append(Spacer(1, 4)) # Μικρό κενό ανάμεσα στα ακίνητα

    story.append(HRFlowable(width="100%", thickness=0.5, color="#ccc", spaceBefore=8, spaceAfter=8))

    # Ενότητα 4: Παρατηρήσεις
    story.append(Paragraph("<b>📝 ΠΑΡΑΤΗΡΗΣΕΙΣ / ΕΙΔΙΚΟΙ ΟΡΟΙ</b>", section_style))
    story.append(Paragraph(lease.notes if lease.notes else "Καμία καταχωρημένη παρατήρηση.", body_style))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color="#ccc", spaceBefore=5, spaceAfter=15))

    # 5. Παραγωγή αρχείου
    doc.build(story)
