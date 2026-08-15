import sys
import datetime
from PySide6.QtGui import QIcon
from PySide6.QtGui import QColor
from PySide6.QtCore import QDate
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolBox
from PySide6.QtWidgets import QTabWidget
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QFormLayout, QGroupBox,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox,
                             QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QDialog, QTextEdit, QScrollArea)
from database import DatabaseManager

from classes.customer import Customer
from classes.property import Property
from classes.lease import Lease
from pdf_generator import generate_lease_pdf

class AddLeaseDialog(QDialog):
    """Φόρμα δημιουργίας νέου συμβολαίου με υποστήριξη δυναμικής προσθήκης πολλαπλών ακινήτων σε TABS"""
    def __init__(self, afm=None, db=None, parent=None):
        super().__init__(parent)
        self.afm = afm
        self.db = db
        # Αυτή η λίστα θα κρατάει τα QLineEdit κάθε ακινήτου που προσθέτει ο χρήστης
        self.prop_forms_list = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle("📝 Νέο Συμφωνητικό Μίσθωσης")
        self.resize(750, 680)
        self.setWindowIcon(QIcon("app_icon.png"))

        main_layout = QVBoxLayout(self)

        # --- ΕΝΟΤΗΤΑ 1: ΒΑΣΙΚΑ ΣΤΟΙΧΕΙΑ ΜΙΣΘΩΣΗΣ ---
        form_layout = QFormLayout()
        self.txt_id = QLineEdit()
        self.txt_id.setPlaceholderText("π.χ. ΜΙΣΘ-2026-001")
        self.txt_type = QLineEdit()
        self.txt_type.setPlaceholderText("π.χ. Κύρια Κατοικία, Επαγγελματική Στέγη")
        self.txt_start = QLineEdit()
        self.txt_start.setPlaceholderText("DD-MM-YYYY")
        self.txt_end = QLineEdit()
        self.txt_end.setPlaceholderText("DD-MM-YYYY")
        self.txt_amount = QLineEdit()
        self.txt_amount.setPlaceholderText("Συνολικό Μηνιαίο Ενοίκιο (€)")

        form_layout.addRow("ID Συμβολαίου:", self.txt_id)
        form_layout.addRow("Είδος / Κατηγορία Μίσθωσης:", self.txt_type)
        form_layout.addRow("Ημερομηνία Έναρξης:", self.txt_start)
        form_layout.addRow("Ημερομηνία Λήξης:", self.txt_end)
        form_layout.addRow("<b>Συνολικό Ενοίκιο (€):</b>", self.txt_amount)
        main_layout.addLayout(form_layout)

        main_layout.addWidget(QLabel("<hr style='border: 0; border-top: 1px solid #ccc;'>"))

        # --- ΕΝΟΤΗΤΑ 2: ΣΥΜΒΑΛΛΟΜΕΝΟΙ (ΑΦΜ) ---
        people_layout = QHBoxLayout()
        self.txt_landlords = QLineEdit()
        self.txt_landlords.setPlaceholderText("ΑΦΜ Ιδιοκτητών χωρισμένα με κόμμα")
        self.txt_tenants = QLineEdit()
        self.txt_tenants.setPlaceholderText("ΑΦΜ Ενοικιαστών χωρισμένα με κόμμα")

        v_l = QVBoxLayout(); v_l.addWidget(QLabel("<b>👑 ΑΦΜ Εκμισθωτών:</b>")); v_l.addWidget(self.txt_landlords)
        v_t = QVBoxLayout(); v_t.addWidget(QLabel("<b>👤 ΑΦΜ Μισθωτών:</b>")); v_t.addWidget(self.txt_tenants)
        people_layout.addLayout(v_l); people_layout.addLayout(v_t)
        main_layout.addLayout(people_layout)

        main_layout.addWidget(QLabel("<hr style='border: 0; border-top: 1px solid #ccc;'>"))

        # --- ΕΝΟΤΗΤΑ 3: ΔΥΝΑΜΙΚΑ ΑΚΙΝΗΤΑ ΜΕ ΚΑΡΤΕΛΕΣ (TABS) ---
        main_layout.addWidget(QLabel("<b>🏠 ΣΤΟΙΧΕΙΑ ΑΚΙΝΗΤΩΝ</b>"))

        # Αντικατάσταση του Scroll Area με QTabWidget
        self.property_input_tabs = QTabWidget()
        self.property_input_tabs.setStyleSheet("""
            QTabBar::tab { background: #f3f3f0; color: #555555; padding: 6px 12px; margin-right: 2px; border: 1px solid #dcdcdc; border-bottom: none; }
            QTabBar::tab:selected { background: white; color: #333333; font-weight: bold; border-top: 2px solid #0078d4; }
        """)
        self.property_input_tabs.setMinimumHeight(200)
        main_layout.addWidget(self.property_input_tabs)

        # Κουμπί για την προσθήκη επιπλέον καρτέλας ακινήτου
        self.btn_add_prop = QPushButton("➕ Προσθήκη Επιπλέον Ακινήτου")
        self.btn_add_prop.setStyleSheet("background-color: #0078d4; color: white; font-weight: bold; padding: 5px;")
        self.btn_add_prop.clicked.connect(self.add_property_form_block)
        main_layout.addWidget(self.btn_add_prop)

        main_layout.addWidget(QLabel("<hr style='border: 0; border-top: 1px solid #ccc;'>"))

        # --- ΕΝΟΤΗΤΑ 4: ΠΑΡΑΤΗΡΗΣΕΙΣ & ΥΠΟΒΟΛΗ ---
        main_layout.addWidget(QLabel("Παρατηρήσεις / Ειδικοί Όροι:"))
        self.txt_notes = QTextEdit()
        self.txt_notes.setMaximumHeight(50)
        main_layout.addWidget(self.txt_notes)

        self.btn_submit = QPushButton("💾 Οριστική Καταχώρηση Μίσθωσης")
        self.btn_submit.setStyleSheet("background-color: #107c41; color: white; font-weight: bold; padding: 8px; font-size: 13px;")
        self.btn_submit.clicked.connect(self.submit_lease)
        main_layout.addWidget(self.btn_submit)

        # Δημιουργούμε αυτόματα το 1ο υποχρεωτικό ακίνητο κατά την εκκίνηση
        self.add_property_form_block()

    def add_property_form_block(self):
        """Δημιουργεί δυναμικά μια νέα καρτέλα (Tab) για την καταχώρηση ενός ακινήτου"""
        next_aa = len(self.prop_forms_list) + 1

        # Κεντρικό widget για το συγκεκριμένο tab
        tab_widget = QWidget()
        box_layout = QVBoxLayout(tab_widget)
        box_layout.setContentsMargins(10, 10, 10, 10)

        # Σειρά 0: Α/Α και Επιμέρους Μίσθωμα
        row0 = QHBoxLayout()
        txt_aa = QLineEdit(str(next_aa))
        txt_aa.setMaximumWidth(40)
        txt_sub_amount = QLineEdit("0.0")
        txt_sub_amount.setMaximumWidth(100)

        row0.addWidget(QLabel("Α/Α:"))
        row0.addWidget(txt_aa)
        row0.addWidget(QLabel("Επιμέρους Μίσθωμα (€):"))
        row0.addWidget(txt_sub_amount)
        row0.addStretch()
        box_layout.addLayout(row0)

        # Σειρά 1: Διεύθυνση
        row1 = QHBoxLayout()
        txt_street = QLineEdit(); txt_street.setPlaceholderText("Οδός")
        txt_number = QLineEdit(); txt_number.setPlaceholderText("Αρ. (π.χ. 12 ή 44-46)")
        txt_area = QLineEdit(); txt_area.setPlaceholderText("Περιοχή")
        txt_pc = QLineEdit(); txt_pc.setPlaceholderText("ΤΚ")

        row1.addWidget(txt_street); row1.addWidget(txt_number); row1.addWidget(txt_area); row1.addWidget(txt_pc)
        box_layout.addLayout(row1)

        # Σειρά 2: Χαρακτηριστικά
        row2 = QHBoxLayout()
        txt_prop_type = QLineEdit(); txt_prop_type.setPlaceholderText("Είδος (π.χ. Διαμέρισμα, Αποθήκη)")
        txt_floor = QLineEdit(); txt_floor.setPlaceholderText("Όροφος")
        txt_sqm = QLineEdit(); txt_sqm.setPlaceholderText("τ.μ.")
        txt_atak = QLineEdit(); txt_atak.setPlaceholderText("ΑΤΑΚ")

        row2.addWidget(txt_prop_type); row2.addWidget(txt_floor); row2.addWidget(txt_sqm); row2.addWidget(txt_atak)
        box_layout.addLayout(row2)

        # Σειρά 3: ΔΕΗ
        row3 = QHBoxLayout()
        txt_dei = QLineEdit(); txt_dei.setPlaceholderText("Αριθμός Παροχής ΔΕΗ (Προαιρετικό)")
        row3.addWidget(QLabel("ΔΕΗ:"))
        row3.addWidget(txt_dei)
        box_layout.addLayout(row3)

        # Προσθήκη του widget ως νέο Tab και αυτόματη εστίαση (επιλογή) σε αυτό
        self.property_input_tabs.addTab(tab_widget, f"Ακίνητο #{next_aa}")
        self.property_input_tabs.setCurrentIndex(next_aa - 1)

        # Αποθήκευση αναφορών στη λίστα για την ανάγνωση κατά το submit
        self.prop_forms_list.append({
            'aa': txt_aa, 'sub_amount': txt_sub_amount, 'street': txt_street,
            'number': txt_number, 'area': txt_area, 'pc': txt_pc,
            'type': txt_prop_type, 'floor': txt_floor, 'sqm': txt_sqm,
            'atak': txt_atak, 'dei': txt_dei
        })

    def submit_lease(self):
        l_id = self.txt_id.text().strip()
        l_type = self.txt_type.text().strip()
        start_raw = self.txt_start.text().strip()
        end_raw = self.txt_end.text().strip()
        amount_raw = self.txt_amount.text().strip()

        if not l_id or not l_type or not start_raw or not end_raw or not amount_raw:
            QMessageBox.warning(self, "Σφάλμα", "Παρακαλώ συμπληρώστε όλα τα βασικά στοιχεία της μίσθωσης!")
            return

        try:
            start_date_obj = datetime.datetime.strptime(start_raw, "%d-%m-%Y").date()
            end_date_obj = datetime.datetime.strptime(end_raw, "%d-%m-%Y").date()
            total_amount = float(amount_raw)
        except ValueError:
            QMessageBox.warning(self, "Σφάλμα", "Οι ημερομηνίες πρέπει να είναι DD-MM-YYYY και το ενοίκιο αριθμός!")
            return

        # 1. Έλεγχος αν το Lease ID υπάρχει ήδη
        if self.db.lease_exists(l_id):
            QMessageBox.critical(self, "Σφάλμα ID", f"Το ID Συμβολαίου '{l_id}' χρησιμοποιείται ήδη!")
            return

        # 2. Ανάγνωση και επικύρωση των ΑΦΜ
        landlord_afms = [x.strip() for x in self.txt_landlords.text().split(",") if x.strip()]
        tenant_afms = [x.strip() for x in self.txt_tenants.text().split(",") if x.strip()]

        if not landlord_afms or not tenant_afms:
            QMessageBox.warning(self, "Σφάλμα", "Πρέπει να εισάγετε τουλάχιστον ένα ΑΦΜ Εκμισθωτή και ένα Μισθωτή!")
            return

        for afm in landlord_afms + tenant_afms:
            if not self.db.customer_exists(afm):
                QMessageBox.critical(self, "Σφάλμα ΑΦΜ", f"Το ΑΦΜ '{afm}' δεν βρέθηκε καταχωρημένο στους Πελάτες!")
                return

        # 3. Δημιουργία του αντικειμένου Lease στη μνήμη
        new_lease = Lease(
            leaseId=l_id, leaseType=l_type, start=start_date_obj,
            end=end_date_obj, amount=total_amount, notes=self.txt_notes.toPlainText().strip()
        )

        # 4. Ανάγνωση και δημιουργία των αντικειμένων Property από τη δυναμική λίστα των Tabs
        parsed_properties = []
        for idx, f in enumerate(self.prop_forms_list):
            street = f['street'].text().strip()
            area = f['area'].text().strip()
            sqm_txt = f['sqm'].text().strip()

            if not street or not area or not sqm_txt:
                # Αυτόματη μεταφορά στην καρτέλα που έχει το σφάλμα για διευκόλυνση του χρήστη
                self.property_input_tabs.setCurrentIndex(idx)
                QMessageBox.warning(self, "Σφάλμα Ακινήτου", f"Παρακαλώ συμπληρώστε Οδό, Περιοχή και τ.μ. στο Ακίνητο #{idx+1}!")
                return

            try:
                aa_val = int(f['aa'].text().strip())
                sub_amt_val = float(f['sub_amount'].text().strip())
                sqm_val = float(sqm_txt)
            except ValueError:
                # Αυτόματη μεταφορά στην καρτέλα με το αριθμητικό σφάλμα
                self.property_input_tabs.setCurrentIndex(idx)
                QMessageBox.warning(self, "Σφάλμα Αριθμών", f"Παρακαλώ εισάγετε έγκυρους αριθμούς για Α/Α, Επιμέρους ενοίκιο και τ.μ. στο Ακίνητο #{idx+1}!")
                return

            # Δημιουργία του Property με το σωστό leaseId σύνδεσης
            prop_obj = Property(
                propertyId=None, leaseId=l_id, aa=aa_val, street=street,
                number=f['number'].text().strip(), area=area, postalCode=f['pc'].text().strip(),
                propertyType=f['type'].text().strip(), floor=f['floor'].text().strip(),
                squareMeters=sqm_val, deiNumber=f['dei'].text().strip(),
                atak=f['atak'].text().strip(), sub_amount=sub_amt_val
            )
            parsed_properties.append(prop_obj)

        # 5. ΟΡΙΣΤΙΚΗ ΕΓΓΡΑΦΗ ΣΤΗ ΒΑΣΗ ΔΕΔΟΜΕΝΩΝ (SQLite)
        # Αποθήκευση του συμβολαίου
        self.db.insert_lease(new_lease)

        # Αποθήκευση όλων των επιμέρους ακινήτων
        for prop in parsed_properties:
            self.db.insert_property(prop)

        # Σύνδεση ιδιοκτητών και ενοικιαστών στους πίνακες m-to-n
        for afm in landlord_afms:
            self.db.link_landlord_to_lease(l_id, afm)
        for afm in tenant_afms:
            self.db.link_tenant_to_lease(l_id, afm)

        QMessageBox.information(
            self,
            "Επιτυχία",
            f"📄 Το συμβόλαιο {l_id} καταχωρήθηκε επιτυχώς με τα {len(parsed_properties)} ακίνητά του!"
        )
        self.accept()


class LeasesDialog(QDialog):
    """Το απόλυτα διορθωμένο παράθυρο συμβολαίων με χρήση Tabs για να φαίνονται όλα πεντακάθαρα"""
    def __init__(self, afm, customer_name, db_manager, parent=None):
        super().__init__(parent) # Correctly links the dialog parent to the main window
        self.afm = afm
        self.customer_name = customer_name
        self.db = db_manager
        self.setWindowTitle(f"Καρτέλα Συμβολαίων: {customer_name}")
        self.resize(950, 650)
        self.initUI()

    def initUI(self):
        self.main_layout = QVBoxLayout()

        self.setWindowIcon(QIcon("app_icon.png"))

        # ΚΟΥΜΠΙ ΠΡΟΣΘΗΚΗΣ ΜΙΣΘΩΤΗΡΙΟΥ (Σταθερό στην κορυφή)
        btn_new_lease = QPushButton("➕ Νέο Μισθωτήριο για αυτόν τον πελάτη")
        btn_new_lease.setStyleSheet("background-color: #0078d4; color: white; font-weight: bold; padding: 8px;")
        btn_new_lease.clicked.connect(self.open_add_lease_dialog)
        self.main_layout.addWidget(btn_new_lease)

        # Χρήση QTabWidget αντί για το προβληματικό QToolBox
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::panel {
                border: 1px solid #dcdcdc;
                background-color: #ffffff;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #f0f0f0;
                border: 1px solid #dcdcdc;
                padding: 8px 15px;
                font-weight: bold;
                color: #0078d4;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #0078d4;
                color: white;
                border-bottom-color: #ffffff;
            }
        """)

        self.main_layout.addWidget(self.tabs)
        self.setLayout(self.main_layout)

        self.load_leases_cards()

    def load_leases_cards(self):
        """Καθαρίζει και φορτώνει τα συμβόλαια μέσα στις καρτέλες (Tabs)"""
        self.tabs.clear()

        self.leases = self.db.get_leases_by_afm(self.afm)

        if not self.leases:
            no_lease_widget = QWidget()
            no_lease_layout = QVBoxLayout()
            no_lease_lbl = QLabel("<h3>Δεν βρέθηκαν ενεργά ή παλαιά μισθωτήρια για αυτόν τον πελάτη.</h3>")
            no_lease_lbl.setStyleSheet("color: gray; padding: 20px;")
            no_lease_layout.addWidget(no_lease_lbl)
            no_lease_widget.setLayout(no_lease_layout)
            self.tabs.addTab(no_lease_widget, "Πληροφορία")
        else:
            for idx, lease in enumerate(self.leases, start=1):
                self.add_lease_to_tabs(lease, idx)

    def reload_ui(self):
        """Καλείται για ανανέωση μετά από νέα καταχώρηση"""
        self.load_leases_cards()

    def open_add_lease_dialog(self):
        """Ανοίγει τη φόρμα προσθήκης και ανανεώνει live την καρτέλα των μισθωτηρίων"""
        dialog = AddLeaseDialog(self.afm, self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.tabs.clear()
            self.load_leases_cards()


    def add_lease_to_tabs(self, lease, idx):
        """Δημιουργεί το περιεχόμενο του συμβολαίου και το βάζει σε αυτόνομο Tab, ελέγχοντας αν έχει λήξει"""
        card_widget = QWidget()
        card_layout = QVBoxLayout()

        # Έλεγχος λήξης συμβολαίου σε σχέση με τη σημερινή ημερομηνία
        import datetime
        today = datetime.date.today()

        # Ορισμός χρώματος ποσού και τίτλου Tab ανάλογα με την κατάσταση
        if lease.end and lease.end < today:
            tab_title = f"❌ [ΛΗΓΜΕΝΟ] Συμβόλαιο {idx} (ID: {lease.leaseId})"
            amount_style = "font-weight: bold; color: #e81123; background-color: #f0f0f0; border: 1px solid #dcdcdc; border-radius: 4px; padding: 2px;"
            status_text = f"<span style='color: #e81123; font-weight: bold;'>[❌ Η ΜΙΣΘΩΣΗ ΕΧΕΙ ΛΗΞΕΙ ΣΤΙΣ {lease.end.strftime('%d-%m-%Y') if isinstance(lease.end, datetime.date) else lease.end}]</span>"
        else:
            tab_title = f"📜 Συμβόλαιο {idx} (ID: {lease.leaseId})"
            amount_style = "font-weight: bold; color: green; background-color: #f0f0f0; border: 1px solid #dcdcdc; border-radius: 4px; padding: 2px;"
            status_text = f"<span style='color: green; font-weight: bold;'>[✅ ΕΝΕΡΓΗ ΜΙΣΘΩΣΗ]</span>"

        # 1. ΕΜΦΑΝΙΣΗ ΕΙΔΟΥΣ ΜΙΣΘΩΣΗΣ & ΚΑΤΑΣΤΑΣΗΣ
        type_lbl = QLabel(f"<b>Κατηγορία: {lease.leaseType}</b> &nbsp;&nbsp;&nbsp;&nbsp; {status_text}")
        type_lbl.setStyleSheet("font-size: 14px; color: #0078d4; margin-bottom: 5px;")
        card_layout.addWidget(type_lbl)

        # 2. ΗΜΕΡΟΜΗΝΙΕΣ & ΠΟΣΟ ΕΝΟΙΚΙΟΥ (Μετατροπή σε ελληνική μορφή DD-MM-YYYY)
        info_layout = QHBoxLayout()
        if isinstance(lease.start, datetime.date):
            start_date_str = lease.start.strftime("%d-%m-%Y")
        else:
            start_date_str = str(lease.start) if lease.start else "Δεν ορίστηκε"

        if isinstance(lease.end, datetime.date):
            end_date_str = lease.end.strftime("%d-%m-%Y")
        else:
            end_date_str = str(lease.end) if lease.end else "Δεν ορίστηκε"

        info_layout.addWidget(QLabel(f"<b>Έναρξη:</b> {start_date_str}"))
        info_layout.addWidget(QLabel(f"<b>Λήξη:</b> {end_date_str}"))
        info_layout.addWidget(QLabel("<b>Ενοίκιο (€):</b>"))

        txt_amount = QLineEdit(str(lease.amount))
        txt_amount.setReadOnly(True)
        txt_amount.setMaximumWidth(80)
        txt_amount.setAlignment(Qt.AlignmentFlag.AlignRight)
        txt_amount.setStyleSheet(amount_style)
        info_layout.addWidget(txt_amount)
        card_layout.addLayout(info_layout)
        card_layout.addWidget(QLabel("<hr style='border: 0; border-top: 1px dashed #ccc;'>"))

        # 3. ΣТОΙΧΕΙΑ ΣΥΜΒΑΛΛΟΜΕΝΩΝ
        people_layout = QHBoxLayout()
        landlord_box = QVBoxLayout()
        landlord_box.addWidget(QLabel("<b>👑 ΕΚΜΙΣΘΩΤΗΣ / ΕΚΜΙΣΘΩΤΕΣ</b>"))
        for landlord in lease.landlords:
            name_str = f"{landlord.firstName} {landlord.lastName}".strip()
            name_display = name_str if name_str else "Καταχωρημένος Πελάτης"
            landlord_box.addWidget(QLabel(f"• {name_display} (ΑΦΜ: {landlord.afm})"))
        people_layout.addLayout(landlord_box)

        tenant_box = QVBoxLayout()
        tenant_box.addWidget(QLabel("<b>👤 ΜΙΣΘΩΤΗΣ / ΜΙΣΘΩΤΕΣ</b>"))
        for tenant in lease.tenants:
            name_str = f"{tenant.firstName} {tenant.lastName}".strip()
            name_display = name_str if name_str else "Καταχωρημένος Πελάτης"
            tenant_box.addWidget(QLabel(f"• {name_display} (ΑΦΜ: {tenant.afm})"))
        people_layout.addLayout(tenant_box)
        card_layout.addLayout(people_layout)
        card_layout.addWidget(QLabel("<hr style='border: 0; border-top: 1px dashed #ccc;'>"))

        # 4. ΣТОΙΧΕΙΑ ΑΚΙΝΗΤΩΝ (Σχεδίαση με εσωτερικές Καρτέλες / Tabs)
        card_layout.addWidget(QLabel("<b>🏠 ΣΤΟΙΧΕΙΑ ΑΚΙΝΗΤΩΝ ΣΥΜΒΟΛΑΙΟΥ (Επεξεργάσιμα)</b>"))

        # Δημιουργία του ΕΣΩΤΕΡΙΚΟΥ Tab Widget για τα ακίνητα
        property_tabs = QTabWidget()
        property_tabs.setStyleSheet("""
            QTabBar::tab { background: #f3f3f0; color: #555555; padding: 6px 12px; margin-right: 2px; border: 1px solid #dcdcdc; border-bottom: none; }
            QTabBar::tab:selected { background: white; color: #333333; font-weight: bold; border-top: 2px solid #0078d4; }
        """)

        all_properties_fields = []

        for p_idx, prop in enumerate(lease.properties):
            tab_widget = QWidget()
            box_layout = QVBoxLayout(tab_widget)
            box_layout.setContentsMargins(10, 10, 10, 10)

            # Σειρά 0: Α/Α και Επιμέρους Μίσθωμα (Εμφανίζονται μόνο αν είναι πάνω από 1 ακίνητο)
            row0_layout = QHBoxLayout()
            txt_aa = QLineEdit(str(prop.aa))
            txt_aa.setMaximumWidth(40)
            txt_sub_amount = QLineEdit(f"{prop.sub_amount:.2f}")
            txt_sub_amount.setMaximumWidth(100)

            if len(lease.properties) > 1:
                row0_layout.addWidget(QLabel("<b>Α/Α:</b>"))
                row0_layout.addWidget(txt_aa)
                row0_layout.addWidget(QLabel("<b>Επιμέρους Μίσθωμα (€):</b>"))
                row0_layout.addWidget(txt_sub_amount)
                row0_layout.addStretch()
                box_layout.addLayout(row0_layout)
            else:
                txt_aa.setVisible(False)
                txt_sub_amount.setVisible(False)

            # Σειρά 1: Οδός, Αρ, Περιοχή, ΤΚ
            row1_layout = QHBoxLayout()
            txt_street = QLineEdit(prop.street)
            txt_number = QLineEdit(prop.number)
            txt_area = QLineEdit(prop.area)
            txt_pc = QLineEdit(prop.postalCode)

            row1_layout.addWidget(QLabel("Οδός:"))
            row1_layout.addWidget(txt_street)
            row1_layout.addWidget(QLabel("Αρ:"))
            row1_layout.addWidget(txt_number)
            row1_layout.addWidget(QLabel("Περιοχή:"))
            row1_layout.addWidget(txt_area)
            row1_layout.addWidget(QLabel("ΤΚ:"))
            row1_layout.addWidget(txt_pc)
            box_layout.addLayout(row1_layout)

            # Σειρά 2: Είδος, Όροφος, τ.μ., ΑΤΑΚ
            row2_layout = QHBoxLayout()
            txt_type = QLineEdit(prop.propertyType)
            txt_floor = QLineEdit(prop.floor)
            txt_sqm = QLineEdit(str(prop.squareMeters))
            txt_atak = QLineEdit(prop.atak if prop.atak else "")
            txt_atak.setPlaceholderText("Δεν ορίστηκε")

            row2_layout.addWidget(QLabel("Είδος:"))
            row2_layout.addWidget(txt_type)
            row2_layout.addWidget(QLabel("Όροφος:"))
            row2_layout.addWidget(txt_floor)
            row2_layout.addWidget(QLabel("τ.μ.:"))
            row2_layout.addWidget(txt_sqm)
            row2_layout.addWidget(QLabel("ΑΤΑΚ:"))
            row2_layout.addWidget(txt_atak)
            box_layout.addLayout(row2_layout)

            # Σειρά 3: ΔΕΗ
            row3_layout = QHBoxLayout()
            txt_dei = QLineEdit(prop.deiNumber if prop.deiNumber else "")
            txt_dei.setPlaceholderText("Δεν ορίστηκε (Αγροτικό)")
            row3_layout.addWidget(QLabel("Αριθμός Παροχής ΔΕΗ:"))
            row3_layout.addWidget(txt_dei)
            box_layout.addLayout(row3_layout)

            # Σύνθεση σταθερού τίτλου εσωτερικής καρτέλας
            # --- ΑΛΛΑΓΗ: Μόνο ο αριθμός του ακινήτου στον τίτλο της εσωτερικής καρτέλας ---
            internal_title = f"Ακίνητο #{p_idx + 1}"

            # Προσθήκη της καρτέλας στο widget των ακινήτων
            property_tabs.addTab(tab_widget, internal_title)

            current_fields = [txt_aa, txt_sub_amount, txt_street, txt_number, txt_area, txt_pc, txt_type, txt_floor, txt_sqm, txt_atak, txt_dei]
            all_properties_fields.append(current_fields)

            for field in current_fields:
                field.setReadOnly(True)
                field.setStyleSheet("background-color: #f0f0f0; border: 1px solid #dcdcdc; border-radius: 4px; padding: 2px;")

        card_layout.addWidget(property_tabs)
        card_layout.addWidget(QLabel("<hr style='border: 0; border-top: 1px dashed #ccc;'>"))

        # 5. ΠΑΡΑΤΗΡΗΣΕΙΣ
        card_layout.addWidget(QLabel("<b>📝 Παρατήρηση / Ειδικοί Όροι:</b>"))
        notes_edit = QTextEdit()
        notes_edit.setText(lease.notes if lease.notes else "")
        notes_edit.setReadOnly(True)
        notes_edit.setMaximumHeight(50)
        card_layout.addWidget(notes_edit)

        # 6. ΚΟΥΜΠΙΑ ΕΝΕΡΓΕΙΩΝ
        buttons_layout = QHBoxLayout()

        btn_edit = QPushButton("✏️ Επεξεργασία Συμβολαίου")
        btn_edit.setStyleSheet("background-color: #0078d4; color: white; font-weight: bold; padding: 6px;")
        btn_edit.clicked.connect(lambda: self.toggle_edit_mode(
            btn_edit, txt_amount, notes_edit, all_properties_fields, lease, type_lbl
        ))
        buttons_layout.addWidget(btn_edit)

        btn_pdf = QPushButton("🖨️ Εκτύπωση σε PDF")
        btn_pdf.setStyleSheet("background-color: #107c41; color: white; font-weight: bold; padding: 6px;")
        btn_pdf.clicked.connect(lambda checked=False, l=lease: self.print_to_pdf_click(l))
        buttons_layout.addWidget(btn_pdf)

        btn_delete_lease = QPushButton("🗑️ Διαγραφή Μίσθωσης")
        btn_delete_lease.setStyleSheet("background-color: #fde7e9; border: 1px solid #e81123; color: #e81123; font-weight: bold; padding: 6px;")

        def direct_delete(l_id=lease.leaseId):
            reply = QMessageBox.question(
                self, "Επιβεβαίωση Διαγραφής Συμβολαίου",
                f"⚠️ ΠΡΟΣΟΧΗ: Είστε απόλυτα σίγουροι ότι θέλετε να διαγράψετε οριστικά το συμβόλαιο με ID '{l_id}';\nΗ ενέργεια αυτή δεν αντιστρέφεται.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.db.delete_lease(l_id)
                    QMessageBox.information(self, "Επιτυχία", f"Το συμβόλαιο {l_id} διαγράφηκε επιτυχώς!")
                    self.tabs.clear()
                    self.load_leases_cards()
                except Exception as e:
                    QMessageBox.critical(self, "Σφάλμα", f"Αδυναμία διαγραφής: {str(e)}")

        btn_delete_lease.clicked.connect(lambda checked=False: direct_delete(lease.leaseId))
        buttons_layout.addWidget(btn_delete_lease)

        card_layout.addWidget(QLabel("<br>"))
        card_layout.addLayout(buttons_layout)
        card_widget.setLayout(card_layout)

        # Προσθήκη ολόκληρης της κάρτας στο κεντρικό widget με τον σωστό τίτλο συμβολαίου
        self.tabs.addTab(card_widget, tab_title)


    def toggle_edit_mode(self, button, txt_amount, notes_edit, all_properties_fields, lease, type_lbl):
        """Διαχειρίζεται το ξεκλείδωμα και την αποθήκευση πολλαπλών ακινήτων ταυτόχρονα"""
        if button.text() == "✏️ Επεξεργασία Συμβολαίου":
            txt_amount.setReadOnly(False)
            notes_edit.setReadOnly(False)
            txt_amount.setStyleSheet("font-weight: bold; color: black; background-color: white; border: 1px solid #0078d4; padding: 2px;")
            notes_edit.setStyleSheet("background-color: white; border: 1px solid #0078d4;")

            # Ξεκλείδωμα ΟΛΩΝ των πεδίων για ΟΛΑ τα ακίνητα
            for prop_fields in all_properties_fields:
                for field in prop_fields:
                    field.setReadOnly(False)
                    field.setStyleSheet("background-color: white; border: 1px solid #0078d4; border-radius: 4px; padding: 2px;")
            button.setText("💾 Αποθήκευση Αλλαγών")
            button.setStyleSheet("background-color: #107c41; color: white; font-weight: bold; padding: 6px; margin-top: 5px;")
        else:
            try:
                new_amount = float(txt_amount.text().strip())

                # Loop για την ανάγνωση και αποθήκευση κάθε ακινήτου ξεχωριστά
                for idx, prop_fields in enumerate(all_properties_fields):
                    prop = lease.properties[idx] # Το αντίστοιχο αντικείμενο Property στη RAM

                    # Μετατροπή αριθμητικών τιμών με βάση τους σωστούς δείκτες της λίστας
                    new_aa = int(prop_fields[0].text().strip())
                    new_sub_amount = float(prop_fields[1].text().strip())
                    new_sqm = float(prop_fields[8].text().strip())

                    # Ενημέρωση των πεδίων του Property από τα QLineEdit
                    prop.aa = new_aa
                    prop.sub_amount = new_sub_amount
                    prop.street = prop_fields[2].text().strip()
                    prop.number = prop_fields[3].text().strip()
                    prop.area = prop_fields[4].text().strip()
                    prop.postalCode = prop_fields[5].text().strip()
                    prop.propertyType = prop_fields[6].text().strip()
                    prop.floor = prop_fields[7].text().strip()
                    prop.squareMeters = new_sqm
                    prop.atak = prop_fields[9].text().strip()
                    prop.deiNumber = prop_fields[10].text().strip()

                    # Αποθήκευση/Ενημέρωση του συγκεκριμένου ακινήτου στην SQLite
                    self.db.insert_property(prop)

                # Ενημέρωση της μίσθωσης
                lease.amount = new_amount
                lease.notes = notes_edit.toPlainText().strip()
                self.db.insert_lease(lease)

                # Κλείδωμα όλων των πεδίων ξανά
                txt_amount.setReadOnly(True)
                notes_edit.setReadOnly(True)
                txt_amount.setStyleSheet("font-weight: bold; color: green; background-color: #f0f0f0; border: 1px solid #dcdcdc; border-radius: 4px; padding: 2px;")
                notes_edit.setStyleSheet("background-color: white; border: 1px solid #dcdcdc;")

                for prop_fields in all_properties_fields:
                    for field in prop_fields:
                        field.setReadOnly(True)
                        field.setStyleSheet("background-color: #f0f0f0; border: 1px solid #dcdcdc; border-radius: 4px; padding: 2px;")

                # ΕΠΑΝΑΦΟΡΑ ΣΩΣΤΟΥ ΤΙΤΛΟΥ ΣΤΗΝ ΚΕΝΤΡΙΚΗ ΚΑΡΤΕΛΑ ΤΗΣ ΚΟΡΥΦΗΣ (Διορθώθηκε ο δείκτης)
                current_tab_index = self.tabs.currentIndex()
                import datetime
                today = datetime.date.today()

                if lease.end and lease.end < today:
                    new_tab_title = f"❌ [ΛΗΓΜΕΝΟ] Συμβόλαιο {current_tab_index + 1} (ID: {lease.leaseId})"
                    status_text = f"<span style='color: #e81123; font-weight: bold;'>[❌ Η ΜΙΣΘΩΣΗ ΕΧΕΙ ΛΗΞΕΙ ΣΤΙΣ {lease.end.strftime('%d-%m-%Y') if isinstance(lease.end, datetime.date) else lease.end}]</span>"
                else:
                    new_tab_title = f"📜 Συμβόλαιο {current_tab_index + 1} (ID: {lease.leaseId})"
                    status_text = f"<span style='color: green; font-weight: bold;'>[✅ ΕΝΕΡΓΗ ΜΙΣΘΩΣΗ]</span>"

                self.tabs.setTabText(current_tab_index, new_tab_title)
                type_lbl.setText(f"<b>Κατηγορία: {lease.leaseType}</b> &nbsp;&nbsp;&nbsp;&nbsp; {status_text}")

                button.setText("✏️ Επεξεργασία Συμβολαίου")
                button.setStyleSheet("background-color: #0078d4; color: white; font-weight: bold; padding: 6px; margin-top: 5px;")

                QMessageBox.information(self, "Επιτυχία", "Τα στοιχεία όλων των ακινήτων αποθηκεύτηκαν επιτυχώς!")
            except ValueError:
                QMessageBox.warning(self, "Σφάλμα", "Ο Α/Α, το ενοίκιο, τα επιμέρους ποσά και τα τ.μ. πρέπει να είναι έγκυροι αριθμοί!")


    def print_to_pdf_click(self, lease):
        """Ανοίγει παράθυρο διαλόγου για να επιλέξει ο χρήστης πού θα αποθηκευτεί το PDF"""
        from PySide6.QtWidgets import QFileDialog

        # Προτεινόμενο όνομα αρχείου
        default_name = f"συμβολαιο_{lease.leaseId}.pdf"

        # Άνοιγμα του επίσημου παραθύρου Save As του λειτουργικού συστήματος
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Αποθήκευση Συμβολαίου σε PDF",
            default_name,
            "Αρχεία PDF (*.pdf)"
        )

        # Αν ο χρήστης πατήσει "Ακύρωση" (Cancel), σταματάμε χωρίς να κάνουμε τίποτα
        if not file_path:
            return

        try:
            # Καλούμε τον generator περνώντας του την πλήρη διαδρομή που επέλεξε ο χρήστης
            generate_lease_pdf(lease, file_path)
            QMessageBox.information(
                self,
                "PDF Έτοιμο",
                f"📄 Το συμβόλαιο αποθηκεύτηκε με επιτυχία!\n\nΔιαδρομή: {file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Σφάλμα PDF", f"Αδυναμία δημιουργίας αρχείου PDF: {str(e)}")

class ExpiringLeasesDialog(QDialog):
    """Το αναβαθμισμένο παράθυρο λήξεων με σταθερό πίνακα και οπτικό εφέ διαχείρισης"""
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.setWindowTitle("Συγκεντρωτικός Πίνακας Λήξεων (Επόμενες 30 ημέρες)")
        self.resize(1150, 450)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setWindowIcon(QIcon("app_icon.png"))

        # ΔΗΜΙΟΥΡΓΙΑ ΠΙΝΑΚΑ: 8 Στήλες (0 έως 7)
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID Μίσθωσης", "Ημ. Λήξης", "Ημέρες", "Ποσό (€)",
            "Εκμισθωτές (Ιδιοκτήτες)", "Μισθωτές (Ενοικιαστές)", "Τηλ", "Διαχειρίστηκε"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)

        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.load_expiring_data()

    def load_expiring_data(self):
        """Φορτώνει τα συμβόλαια που λήγουν και εφαρμόζει σταθερή εμφάνιση"""
        summary = self.db.get_all_expiring_leases_summary(days_threshold=30)
        self.table.setRowCount(0)

        import datetime
        for row_idx, r in enumerate(summary):
            self.table.insertRow(row_idx)

            # 1. ID, 2. Ημερομηνία, 3. Ημέρες
            self.table.setItem(row_idx, 0, QTableWidgetItem(r['lease_id']))

            raw_date = r['end_date']
            try:
                date_obj = datetime.datetime.strptime(raw_date, "%Y-%m-%d").date() if "-" in raw_date else datetime.date.fromisoformat(raw_date)
                greek_date_str = date_obj.strftime("%d-%m-%Y")
            except Exception:
                greek_date_str = raw_date

            self.table.setItem(row_idx, 1, QTableWidgetItem(greek_date_str))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(r['days_left'])))

            # 4. Ποσό
            amount_item = QTableWidgetItem(f"{r['amount']:.2f} €")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVertical_Mask)
            self.table.setItem(row_idx, 3, amount_item)

            # 5. Εκμισθωτές & 6. Μισθωτές
            self.table.setItem(row_idx, 4, QTableWidgetItem(", ".join(r['landlords'])))
            self.table.setItem(row_idx, 5, QTableWidgetItem(", ".join(r['tenants'])))

            # 7. Φακός 🔍
            btn_view_contact = QPushButton("🔍")
            btn_view_contact.setStyleSheet("background-color: #f3f3f0; border: 1px solid #a19f9d; border-radius: 3px; max-width: 30px; padding: 2px;")
            btn_view_contact.clicked.connect(lambda checked=False, l_id=r['lease_id']: LeaseContactDialog(l_id, self.db).exec())
            self.table.setCellWidget(row_idx, 6, btn_view_contact)

            # 8. Κουμπί Checkbox Διαχείρισης
            from PySide6.QtWidgets import QCheckBox
            chk_managed = QCheckBox()

            # Ανάγνωση τρέχουσας κατάστασης από τη βάση
            is_active = (r.get('is_managed', 0) == 1)
            chk_managed.setChecked(is_active)

            # Αν είναι ήδη αρχειοθετημένο, θολώνει live τη γραμμή εξ αρχής
            if is_active:
                for col in range(6):
                    item = self.table.item(row_idx, col)
                    if item: item.setForeground(QColor("#888888"))

            # Σύνδεση live αλλαγής χρώματος χωρίς μετακίνηση δεδομένων
            def make_toggle_fn(l_id, current_row):
                return lambda checked: self.update_row_visual(checked, l_id, current_row)

            chk_managed.toggled.connect(make_toggle_fn(r['lease_id'], row_idx))
            self.table.setCellWidget(row_idx, 7, chk_managed)

    def update_row_visual(self, checked, lease_id, row):
        """Ενημερώνει τη βάση και αλλάζει το χρώμα της γραμμής live"""
        status = 1 if checked else 0
        self.db.update_lease_managed_status(lease_id, status)

        # Αλλαγή χρώματος κειμένου live
        color = QColor("#888888") if checked else QColor("black")
        for col in range(6):
            item = self.table.item(row, col)
            if item:
                item.setForeground(color)

class ExpiredLeasesDialog(QDialog):
    """Αναδυόμενο παράθυρο που εμφανίζει συγκεντρωτικά όλα τα ληγμένα συμβόλαια"""
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle("🗑️ Ληγμένα Συμβόλαια (Ιστορικό)")
        self.resize(1000, 450)
        self.setWindowIcon(QIcon("app_icon.png"))

        layout = QVBoxLayout(self)

        header = QLabel("<b>⚠️ ΛΙΣΤΑ ΣΥΜΒΟΛΑΙΩΝ ΠΟΥ ΕΧΟΥΝ ΛΗΞΕΙ</b>")
        header.setStyleSheet("font-size: 14px; color: #e81123;")
        layout.addWidget(header)

        # Πίνακας 7 στηλών
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID Συμβολαίου", "Ημ. Λήξης", "Ποσό (€)", "Εκμισθωτές", "Μισθωτές", "Επικοινωνία", "Διαχειρίστηκε"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(28)
        layout.addWidget(self.table)

        self.load_expired_data()

    def load_expired_data(self):
        """Φορτώνει τα ληγμένα δεδομένα και κρατάει σταθερή τη λίστα"""
        summary = self.db.get_all_expired_leases_summary()
        self.table.setRowCount(0)

        import datetime
        for row_idx, r in enumerate(summary):
            self.table.insertRow(row_idx)

            # 1. ID
            self.table.setItem(row_idx, 0, QTableWidgetItem(r['lease_id']))

            # 2. Ημερομηνία
            raw_date = r['end_date']
            try:
                date_obj = datetime.date.fromisoformat(raw_date)
                greek_date_str = date_obj.strftime("%d-%m-%Y")
            except Exception:
                greek_date_str = raw_date
            self.table.setItem(row_idx, 1, QTableWidgetItem(greek_date_str))

            # 3. Ποσό
            amount_item = QTableWidgetItem(f"{r['amount']:.2f} €")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVertical_Mask)
            amount_item.setForeground(QColor("#e81123"))
            self.table.setItem(row_idx, 2, amount_item)

            # 4. Εκμισθωτές & 5. Μισθωτές
            self.table.setItem(row_idx, 3, QTableWidgetItem(", ".join(r['landlords'])))
            self.table.setItem(row_idx, 4, QTableWidgetItem(", ".join(r['tenants'])))

            # 6. Φακός 🔍
            btn_view_contact = QPushButton("🔍")
            btn_view_contact.setStyleSheet("background-color: #f3f3f0; border: 1px solid #a19f9d; border-radius: 3px; max-width: 30px; padding: 2px;")
            btn_view_contact.clicked.connect(lambda checked=False, l_id=r['lease_id']: LeaseContactDialog(l_id, self.db).exec())
            self.table.setCellWidget(row_idx, 5, btn_view_contact)

            # 7. Κουμπί Checkbox Διαχείρισης
            from PySide6.QtWidgets import QCheckBox
            chk_managed = QCheckBox()

            # Διαβάζει την τρέχουσα κατάσταση από τη βάση (αν r['is_managed'] == 1 τότε είναι τσεκαρισμένο)
            is_active = (r.get('is_managed', 0) == 1)
            chk_managed.setChecked(is_active)

            # Έξυπνο οπτικό εφέ: Αν είναι ήδη διαχειρισμένο, θολώνει ελαφρώς τη γραμμή
            if is_active:
                for col in range(5):
                    item = self.table.item(row_idx, col)
                    if item: item.setForeground(QColor("#888888"))

            # Όταν ο χρήστης κάνει κλικ, αλλάζει το χρώμα live και αποθηκεύει στη βάση χωρίς να μετακινεί τίποτα!
            def make_toggle_fn(l_id, current_row):
                return lambda checked: self.update_row_visual(checked, l_id, current_row)

            chk_managed.toggled.connect(make_toggle_fn(r['lease_id'], row_idx))
            self.table.setCellWidget(row_idx, 6, chk_managed)

    def update_row_visual(self, checked, lease_id, row):
        """Ενημερώνει τη βάση και αλλάζει το χρώμα της γραμμής live χωρίς μπερδέματα"""
        status = 1 if checked else 0
        self.db.update_lease_managed_status(lease_id, status)

        # Αλλαγή χρώματος κειμένου live
        color = QColor("#888888") if checked else QColor("black")
        for col in range(5):
            item = self.table.item(row, col)
            if item:
                # Κρατάμε το κόκκινο χρώμα στο ποσό αν ξε-τσεκαριστεί
                if col == 2 and not checked:
                    item.setForeground(QColor("#e81123"))
                else:
                    item.setForeground(color)


class LeaseContactDialog(QDialog):
    """Παράθυρο που δείχνει ΜΟΝΟ τα στοιχεία επικοινωνίας για τα συμβόλαια που λήγουν"""
    def __init__(self, lease_id, db_manager):
        super().__init__()
        self.lease_id = lease_id
        self.db = db_manager
        self.setWindowTitle(f"Στοιχεία Επικοινωνίας Συμβολαίου: {lease_id}")
        self.resize(500, 400)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        title = QLabel(f"<h3>📞 Τηλέφωνα Επικοινωνίας (ID Μίσθωσης: {self.lease_id})</h3>")
        title.setStyleSheet("color: #d83b01; margin-bottom: 5px;")
        layout.addWidget(title)

        self.setWindowIcon(QIcon("app_icon.png"))

        # Ανάκτηση του συγκεκριμένου συμβολαίου με όλους τους συμβαλλόμενους από τη βάση
        # Ψάχνουμε με ένα dummy ΑΦΜ για να μας φέρει το συμβόλαιο, ή φιλτράρουμε
        all_leases = self.db.get_leases_by_afm("") # Παράκαμψη, ή ζητάμε απευθείας από τη λίστα
        # Για απόλυτη ακρίβεια, φτιάχνουμε μια γρήγορη ανάγνωση των στοιχείων των τηλεφώνων

        # Επειδή έχουμε το lease_id, θα εμφανίσουμε τους ιδιοκτήτες και ενοικιαστές με τα τηλέφωνά τους
        # Για να μην αλλάξουμε το database.py, τραβάμε τα στοιχεία απευθείας από την SQLite
        query = """
            SELECT '👑 Ιδιοκτήτης', c.firstName || ' ' || c.lastName, c.phone, c.afm FROM lease_landlords ll
            INNER JOIN customers c ON ll.landlord_afm = c.afm WHERE ll.lease_id = ?
            UNION
            SELECT '👤 Ενοικιαστής', c.firstName || ' ' || c.lastName, c.phone, c.afm FROM lease_tenants lt
            INNER JOIN customers c ON lt.tenant_afm = c.afm WHERE lt.lease_id = ?;
        """

        layout.addWidget(QLabel("<b>Λίστα Συμβαλλόμενων & Τηλέφωνα:</b>"))

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (self.lease_id, self.lease_id))
            rows = cursor.fetchall()

            for role, name, phone, afm in rows:
                card = QWidget()
                card.setStyleSheet("background-color: #f3f3f0; border: 1px solid #dcdcdc; border-radius: 4px; padding: 8px;")
                card_layout = QVBoxLayout()

                card_layout.addWidget(QLabel(f"<b>{role}:</b> {name}"))
                card_layout.addWidget(QLabel(f"<b>📱 Τηλέφωνο:</b> <span style='font-size: 13px; color: #0078d4; font-weight: bold;'>{phone if phone else '-'}</span>"))
                card_layout.addWidget(QLabel(f"<b>ΑΦΜ:</b> {afm}"))

                card.setLayout(card_layout)
                layout.addWidget(card)

        # Κουμπί Κλεισίματος
        btn_close = QPushButton("Κλείσιμο")
        btn_close.setStyleSheet("background-color: #d83b01; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        self.setLayout(layout)


class AddCustomerDialog(QDialog):
    """Παράθυρο για την προσθήκη νέου πελάτη με έλεγχο ύπαρξης ΑΦΜ"""
    def __init__(self, db_manager, parent_window):
        super().__init__()
        self.db = db_manager
        self.parent_win = parent_window
        self.setWindowTitle("➕ Προσθήκη Νέου Πελάτη")
        self.resize(350, 300)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.setWindowIcon(QIcon("app_icon.png"))

        self.txt_afm = QLineEdit()
        self.txt_afm.setPlaceholderText("ΑΦΜ (9 ψηφία)")
        layout.addWidget(QLabel("ΑΦΜ:"))
        layout.addWidget(self.txt_afm)

        self.txt_first = QLineEdit()
        layout.addWidget(QLabel("Όνομα:"))
        layout.addWidget(self.txt_first)

        self.txt_last = QLineEdit()
        layout.addWidget(QLabel("Επώνυμο:"))
        layout.addWidget(self.txt_last)

        self.txt_father = QLineEdit()
        layout.addWidget(QLabel("Όνομα Πατρός:"))
        layout.addWidget(self.txt_father)

        self.txt_mother = QLineEdit()
        layout.addWidget(QLabel("Όνομα Μητρός:"))
        layout.addWidget(self.txt_mother)

        self.txt_phone = QLineEdit()
        layout.addWidget(QLabel("Τηλέφωνο:"))
        layout.addWidget(self.txt_phone)

        self.cmb_active = QComboBox()
        self.cmb_active.addItems(["Ενεργός", "Ανενεργός"])
        layout.addWidget(QLabel("Κατάσταση Πελάτη:"))
        layout.addWidget(self.cmb_active)

        btn_add = QPushButton("Καταχώρηση")
        btn_add.setStyleSheet("background-color: #107c41; color: white; font-weight: bold; padding: 6px;")
        btn_add.clicked.connect(self.add_customer)
        layout.addWidget(btn_add)

        self.setLayout(layout)

    def add_customer(self):
        afm = self.txt_afm.text().strip()
        first = self.txt_first.text().strip()
        last = self.txt_last.text().strip()

        if not afm or not first or not last:
            QMessageBox.warning(self, "Σφάλμα", "Τα πεδία ΑΦΜ, Όνομα και Επώνυμο είναι υποχρεωτικά!")
            return

        # Έλεγχος αν υπάρχει ήδη το ΑΦΜ στη βάση δεδομένων
        if self.db.customer_exists(afm):
            QMessageBox.warning(self, "Αδυναμία Καταχώρησης", f"Υπάρχει ήδη καταχωρημένος πελάτης με ΑΦΜ: {afm}!")
            return

            # Μέσα στην add_customer της AddCustomerDialog:
        active_val = 1 if self.cmb_active.currentText() == "Ενεργός" else 0

        new_cust = Customer(
            firstName=first, lastName=last,
            fatherName=self.txt_father.text().strip(),
            motherName=self.txt_mother.text().strip(),
            afm=afm, phone=self.txt_phone.text().strip(),
            isActive=active_val # <--- ΑΠΟΘΗΚΕΥΣΗ ΚΑΤΑΣΤΑΣΗΣ
        )

        self.db.insert_customer(new_cust)
        QMessageBox.information(self, "Επιτυχία", "O πελάτης καταχωρήθηκε επιτυχώς!")
        # Αντικαταστήστε τη γραμμή self.parent_win.refresh_data() με:
        self.parent_win.load_customer_data() # <--- ΣΩΣΤΗ ΚΛΗΣΗ ΑΝΑΝΕΩΣΗΣ
        self.accept()

class CustomerDetailsDialog(QDialog):
    """Το αναβαθμισμένο παράθυρο στοιχείων πελάτη με δυνατότητα ΠΛΗΡΟΥΣ ΕΠΕΞΕΡΓΑΣΙΑΣ (Edit)"""
    def __init__(self, customer, db_manager, parent_window=None):
        # ΔΙΟΡΘΩΣΗ: Περνάμε το parent_window απευθείας στη super() της Qt
        super().__init__(parent_window)
        self.customer = customer
        self.db = db_manager
        self.parent_win = parent_window # Κρατάμε και τη ρητή αναφορά
        self.setWindowTitle(f"Προσωπικά Στοιχεία: {customer.firstName} {customer.lastName}")
        self.resize(400, 500)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)

        title = QLabel("<h3>📇 Πλήρη Στοιχεία Πελάτη</h3>")
        title.setStyleSheet("color: #0078d4; margin-bottom: 5px;")
        layout.addWidget(title)

        self.setWindowIcon(QIcon("app_icon.png"))

        # 1. Δημιουργία των πεδίων κειμένου
        layout.addWidget(QLabel("<b>Α.Φ.Μ. (Κλειδί - Μη επεξεργάσιμο):</b>"))
        self.txt_afm = QLineEdit(self.customer.afm)
        self.txt_afm.setReadOnly(True)
        self.txt_afm.setStyleSheet("background-color: #e1dfdd; border: 1px solid #dcdcdc; border-radius: 4px; padding: 4px; color: #505050;")
        layout.addWidget(self.txt_afm)

        layout.addWidget(QLabel("<b>Επώνυμο:</b>"))
        self.txt_last = QLineEdit(self.customer.lastName)
        layout.addWidget(self.txt_last)

        layout.addWidget(QLabel("<b>Όνομα:</b>"))
        self.txt_first = QLineEdit(self.customer.firstName)
        layout.addWidget(self.txt_first)

        layout.addWidget(QLabel("<b>Όνομα Πατρός:</b>"))
        self.txt_father = QLineEdit(self.customer.fatherName if self.customer.fatherName else "")
        layout.addWidget(self.txt_father)

        layout.addWidget(QLabel("<b>Όνομα Μητρός:</b>"))
        self.txt_mother = QLineEdit(self.customer.motherName if self.customer.motherName else "")
        layout.addWidget(self.txt_mother)

        layout.addWidget(QLabel("<b>Τηλέφωνο Επικοινωνίας:</b>"))
        self.txt_phone = QLineEdit(self.customer.phone if self.customer.phone else "")
        layout.addWidget(self.txt_phone)

        # Μέσα στην initUI της CustomerDetailsDialog:
        layout.addWidget(QLabel("<b>Κατάσταση Πελάτη:</b>"))
        self.cmb_active = QComboBox()
        self.cmb_active.addItems(["Ενεργός", "Ανενεργός"])
        self.cmb_active.setCurrentText("Ενεργός" if self.customer.isActive == 1 else "Ανενεργός")
        layout.addWidget(self.cmb_active)

        # Προσθέστε το cmb_active στη λίστα edit_fields για να ξεκλειδώνει
        self.edit_fields = [self.txt_last, self.txt_first, self.txt_father, self.txt_mother, self.txt_phone, self.cmb_active]

        # --- ΔΙΟΡΘΩΣΗ ΚΛΕΙΔΩΜΑΤΟΣ ΠΕΔΙΩΝ ---
        # Αρχικό κλείδωμα όλων των πεδίων (Read-Only για QLineEdit, Disabled για QComboBox)
        for field in self.edit_fields:
            if isinstance(field, QComboBox):
                field.setEnabled(False) # Το QComboBox κλειδώνει με setEnabled(False)
                field.setStyleSheet("background-color: #f0f0f0; color: #555555; border: 1px solid #dcdcdc; border-radius: 4px; padding: 2px;")
            else:
                field.setReadOnly(True) # Τα QLineEdit κλειδώνουν κανονικά με setReadOnly(True)
                field.setStyleSheet("background-color: #f0f0f0; border: 1px solid #dcdcdc; border-radius: 4px; padding: 2px;")

        # 2. ΚΟΥΜΠΙΑ ΕΝΕΡΓΕΙΩΝ (Οριζόντια διάταξη στο κάτω μέρος)
        buttons_layout = QHBoxLayout()

        # Κουμπί Edit / Save
        self.btn_edit = QPushButton("✏️ Επεξεργασία Στοιχείων")
        self.btn_edit.setStyleSheet("background-color: #0078d4; color: white; font-weight: bold; padding: 6px;")
        self.btn_edit.clicked.connect(self.toggle_customer_edit)
        buttons_layout.addWidget(self.btn_edit)

        # Κουμπί Κλεισίματος
        btn_close = QPushButton("Κλείσιμο")
        btn_close.setStyleSheet("background-color: #a19f9d; color: black; font-weight: bold; padding: 6px;")
        btn_close.clicked.connect(self.accept)
        buttons_layout.addWidget(btn_close)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def toggle_customer_edit(self):
        """Εναλλάσσει τη λειτουργία ανάμεσα σε επεξεργασία και αποθήκευση στοιχείων πελάτη"""
        from PySide6.QtWidgets import QComboBox # Σιγουρευόμαστε για το import

        if self.btn_edit.text() == "✏️ Επεξεργασία Στοιχείων":
            # ΞΕΚΛΕΙΔΩΜΑ ΠΕΔΙΩΝ (Με έλεγχο για το QComboBox)
            for field in self.edit_fields:
                if isinstance(field, QComboBox):
                    field.setEnabled(True) # Το QComboBox ξεκλειδώνει με setEnabled(True)
                else:
                    field.setReadOnly(False) # Τα QLineEdit ξεκλειδώνουν με setReadOnly(False)
                field.setStyleSheet("background-color: white; border: 1px solid #0078d4; border-radius: 4px; padding: 2px;")

            self.btn_edit.setText("💾 Αποθήκευση Αλλαγών")
            self.btn_edit.setStyleSheet("background-color: #107c41; color: white; font-weight: bold; padding: 6px;")
        else:
            # ΑΠΟΘΗΚΕΥΣΗ ΑΛΛΑΓΩΝ
            self.customer.lastName = self.txt_last.text().strip()
            self.customer.firstName = self.txt_first.text().strip()
            self.customer.fatherName = self.txt_father.text().strip()
            self.customer.motherName = self.txt_mother.text().strip()
            self.customer.phone = self.txt_phone.text().strip()

            # Ανάγνωση της τιμής από το QComboBox
            self.customer.isActive = 1 if self.cmb_active.currentText() == "Ενεργός" else 0

            # Ενημέρωση στη βάση δεδομένων
            self.db.insert_customer(self.customer)

            # ΚΛΕΙΔΩΜΑ ΠΕΔΙΩΝ ΞΑΝΑ (Με έλεγχο για το QComboBox)
            for field in self.edit_fields:
                if isinstance(field, QComboBox):
                    field.setEnabled(False)
                else:
                    field.setReadOnly(True)
                field.setStyleSheet("background-color: #f0f0f0; border: 1px solid #dcdcdc; border-radius: 4px; padding: 2px;")

            self.btn_edit.setText("✏️ Επεξεργασία Στοιχείων")
            self.btn_edit.setStyleSheet("background-color: #0078d4; color: white; font-weight: bold; padding: 6px;")

            if self.parent():
                self.parent().load_customer_data()
                self.parent().table.clearSelection() # Καθαρίζει τυχόν παλιό κλείδωμα επιλογής


            QMessageBox.information(self, "Επιτυχία", "Τα στοιχεία του πελάτη ενημερώθηκαν επιτυχώς!")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.all_customers = [] # Μνήμη RAM για ακαριαίο φιλτράρισμα
        # Στο τέλος της __init__ της MainWindow αλλάξτε σε:
        self.initUI()
        self.load_customer_data() # <--- ΑΥΤΟΜΑΤΟ ΦΙΛΤΡΑΡΙΣΜΑ ΚΑΤΑ ΤΗΝ ΕΚΚΙΝΗΣΗ

    def initUI(self):
        self.setWindowTitle("Σύστημα Διαχείρισης Μισθωτηρίων")
        self.resize(1020, 600) # Μεγαλώσαμε ελάχιστα το πλάτος για τη νέα στήλη

        self.setWindowIcon(QIcon("app_icon.png"))

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # --- ΠΑΝΩ ΜΕΡΟΣ: ΑΝΑΖΗΤΗΣΗ, ΚΟΥΜΠΙ + ΚΑΙ ΚΟΥΜΠΙ ΛΗΞΕΩΝ ---
        top_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Αναζήτηση με βάση το Ονοματεπώνυμο ή το ΑΦΜ...")
        self.txt_search.textChanged.connect(self.filter_customers)
        top_layout.addWidget(self.txt_search, 4)

        # Μέσα στην initUI της MainWindow, κάτω από το main_layout.addLayout(top_layout):
        from PySide6.QtWidgets import QRadioButton, QButtonGroup

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("<b>Προβολή Πελατών:</b>"))

        self.btn_filter_all = QRadioButton("Όλοι")
        self.btn_filter_active = QRadioButton("Μόνο Ενεργοί")
        self.btn_filter_inactive = QRadioButton("Μόνο Ανενεργοί")
        self.btn_filter_active.setChecked(True) # Προεπιλογή: Να δείχνει τους ενεργούς

        # Ομαδοποίηση κουμπιών
        self.filter_group = QButtonGroup(self)
        self.filter_group.addButton(self.btn_filter_all)
        self.filter_group.addButton(self.btn_filter_active)
        self.filter_group.addButton(self.btn_filter_inactive)

        filter_layout.addWidget(self.btn_filter_all)
        filter_layout.addWidget(self.btn_filter_active)
        filter_layout.addWidget(self.btn_filter_inactive)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Σύνδεση των κλικ με τη μέθοδο φιλτραρίσματος
        self.btn_filter_all.toggled.connect(self.filter_customers)
        self.btn_filter_active.toggled.connect(self.filter_customers)
        self.btn_filter_inactive.toggled.connect(self.filter_customers)


        btn_add_cust = QPushButton("➕ Νέος Πελάτης")
        btn_add_cust.setStyleSheet("background-color: #107c41; color: white; font-weight: bold; padding: 6px;")
        btn_add_cust.clicked.connect(self.open_add_customer_dialog)
        top_layout.addWidget(btn_add_cust, 1)

        btn_expiring = QPushButton("📅 Συμβόλαια που Λήγουν")
        btn_expiring.setStyleSheet("background-color: #d83b01; color: white; font-weight: bold; padding: 6px;")
        btn_expiring.clicked.connect(self.open_expiring_dialog)
        top_layout.addWidget(btn_expiring, 1)

        # Κάτω από το κουμπί btn_expiring:
        self.btn_expired = QPushButton("🗑️ Συμβόλαια Ληγμένα")
        self.btn_expired.setStyleSheet("background-color: #fde7e9; border: 1px solid #e81123; color: #e81123; font-weight: bold; padding: 6px;")
        self.btn_expired.clicked.connect(self.open_expired_dialog)
        top_layout.addWidget(self.btn_expired) # Προσθήκη δίπλα στο άλλο

        main_layout.addLayout(top_layout)

        # --- ΚΑΤΩ ΜΕΡΟΣ: ΚΕΝΤΡΙΚΟΣ ΠΙΝΑΚΑΣ ΠΕΛΑΤΩΝ (Μετονομασία & 6 Στήλες) ---
        # Μέσα στην initUI της κλάσης MainWindow:
        self.table = QTableWidget()
        self.table.setColumnCount(6)

        # ----------------------------------------------------------------------
        # ΝΕΕΣ ΠΡΟΣΘΗΚΕΣ ΓΙΑ ΑΠΟΛΥΤΟ SCROLL ΚΑΙ ΑΝΕΣΗ ΣΕ ΠΟΛΛΟΥΣ ΠΕΛΑΤΕΣ
        # ----------------------------------------------------------------------
        # 1. Εξασφαλίζει ότι η κάθετη μπάρα scroll θα εμφανίζεται αυτόματα μόλις χρειαστεί
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 2. Κάνει τις γραμμές του πίνακα να έχουν ένα ομοιόμορφο, καθαρό ύψος (π.χ. 28 pixels)
        self.table.verticalHeader().setDefaultSectionSize(28)

        # 3. Απλώνει τις στήλες ώστε να πιάνουν όλο το πλάτος της οθόνης χωρίς κενά
        self.table.horizontalHeader().setStretchLastSection(True)
        # ----------------------------------------------------------------------

        self.table.setHorizontalHeaderLabels(["ΑΦΜ", "Επώνυμο", "Όνομα", "Τηλέφωνο", "Στοιχεία", "Διαγραφή"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Κλείδωμα πλάτους για τις δύο τελευταίες στήλες των ενεργειών
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) # Στήλη Φακού
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents) # Στήλη Διαγραφής

        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemDoubleClicked.connect(self.open_customer_leases)

        main_layout.addWidget(self.table)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def refresh_data(self):
        """Ανακατευθύνει την παλιά refresh_data στη σωστή μέθοδο φιλτραρίσματος"""
        self.load_customer_data()

    def update_table_display(self, customers_list):
        """Ενημερώνει τα δεδομένα και δημιουργεί τα κουμπιά Ενεργειών (Φακός και Διαγραφή)"""
        self.table.setRowCount(0)
        for row_idx, customer in enumerate(customers_list):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(customer.afm))
            self.table.setItem(row_idx, 1, QTableWidgetItem(customer.lastName))
            self.table.setItem(row_idx, 2, QTableWidgetItem(customer.firstName))
            self.table.setItem(row_idx, 3, QTableWidgetItem(customer.phone))

            # 1. ΔΗΜΙΟΥΡΓΙΑ ΚΟΥΜΠΙΟΥ ΦΑΚΟΥ (🔍) - ΜΕ ΣΩΣΤΗ ΔΙΑΣΥΝΔΕΣΗ ΓΙΑ EDIT
            btn_view = QPushButton("🔍")
            btn_view.setToolTip("Προβολή Προσωπικών Στοιχείων")
            btn_view.setStyleSheet("background-color: #e1dfdd; border: 1px solid #a19f9d; border-radius: 3px; max-width: 30px; padding: 2px;")

            # Περνάμε το c (customer), το self.db (βάση) και το self (αρχική οθόνη για ανανέωση)
            btn_view.clicked.connect(lambda checked=False, c=customer: CustomerDetailsDialog(c, self.db, self).exec())
            self.table.setCellWidget(row_idx, 4, btn_view)

            # 2. ΔΗΜΙΟΥΡΓΙΑ ΚΟΥΜΠΙΟΥ ΔΙΑΓΡΑΦΗΣ (❌)
            btn_delete = QPushButton("❌")
            btn_delete.setToolTip("Διαγραφή Πελάτη")
            btn_delete.setStyleSheet("background-color: #fde7e9; border: 1px solid #e81123; border-radius: 3px; max-width: 30px; padding: 2px;")
            btn_delete.clicked.connect(lambda checked=False, a=customer.afm, n=f"{customer.firstName} {customer.lastName}": self.delete_customer_click(a, n))
            self.table.setCellWidget(row_idx, 5, btn_delete)

    def filter_customers(self):
        """Φιλτράρει live τη λίστα συνδυάζοντας την αναζήτηση κειμένου και το Radio Button κατάστασης"""
        search_text = self.txt_search.text().lower().strip()

        filtered = []
        for c in self.all_customers:
            # 1. Έλεγχος Φίλτρου Κατάστασης (Radio Buttons)
            if self.btn_filter_active.isChecked() and c.isActive == 0:
                continue
            if self.btn_filter_inactive.isChecked() and c.isActive == 1:
                continue

            # 2. Έλεγχος Κειμένου Αναζήτησης
            full_name = f"{c.firstName} {c.lastName}".lower()
            if not search_text or (search_text in full_name or search_text in c.afm):
                filtered.append(c)

        self.update_table_display(filtered)

    def open_customer_leases(self, item):
        """Εκτελείται στο διπλό κλικ και ανοίγει την αναλυτική καρτέλα συμβολαίων"""
        row = item.row()
        afm = self.table.item(row, 0).text()
        last_name = self.table.item(row, 1).text()
        first_name = self.table.item(row, 2).text()

        # ΔΙΟΡΘΩΣΗ: Προσθήκη του , self στο τέλος για σωστό window parent linking
        dialog = LeasesDialog(afm, f"{first_name} {last_name}", self.db, self)
        dialog.exec()

    def open_add_customer_dialog(self):
        """Ανοίγει το παράθυρο φόρμας για προσθήκη νέου προσώπου"""
        dialog = AddCustomerDialog(self.db, self)
        dialog.exec()

    def open_expiring_dialog(self):
        """Ανοίγει τον συγκεντρωτικό πίνακα λήξεων"""
        dialog = ExpiringLeasesDialog(self.db)
        dialog.exec()

    def delete_customer_click(self, afm, full_name):
        """Ελέγχει αν ο πελάτης δεσμεύεται σε συμβόλαια και εκτελεί τη διαγραφή"""
        # Έλεγχος ασφαλείας: Συμμετέχει ο πελάτης σε κάποια μίσθωση (ως landlord ή tenant);
        if self.db.has_active_leases(afm):
            QMessageBox.critical(
                self,
                "Αδυναμία Διαγραφής",
                f"Ο πελάτης '{full_name}' δεν μπορεί να διαγραφεί επειδή είναι καταχωρημένος ως συμβαλλόμενος σε ενεργό ή παλαιό μισθωτήριο συμβόλαιο!"
            )
            return

        # Μήνυμα επιβεβαίωσης
        reply = QMessageBox.question(
            self,
            "Επιβεβαίωση Διαγραφής",
            f"Είστε σίγουρος ότι θέλετε να διαγράψετε οριστικά τον πελάτη '{full_name}';",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.db.delete_customer(afm)
            self.refresh_data() # Ανανέωση του πίνακα στην οθόνη

    def open_expired_dialog(self):
        """Ανοίγει το παράθυρο με το ιστορικό των ληγμένων συμβολαίων"""
        dialog = ExpiredLeasesDialog(self.db, self)
        dialog.exec()

    def load_customer_data(self):
        """Φορτώνει όλους τους πελάτες από τη βάση στη μνήμη και εφαρμόζει live το φίλτρο"""
        self.all_customers = self.db.get_all_customers()

        # ΔΙΟΡΘΩΣΗ: Αντί να τους δείχνει χύμα όλους, καλεί το φίλτρο για να σεβαστεί το Radio Button
        self.filter_customers()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
