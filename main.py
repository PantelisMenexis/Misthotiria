from datetime import date, timedelta
from classes.customer import Customer
from classes.property import Property
from classes.lease import Lease
from database import DatabaseManager

def test_summary_table():
    db = DatabaseManager()

    # Δεδομένα για το 1ο Συμβόλαιο (Λήγει σε 5 μέρες)
    owner1 = Customer(firstName="Γιάννης", lastName="Παπαδόπουλος", afm="123456789", phone="69111")
    tenant1 = Customer(firstName="Μαρία", lastName="Γεωργίου", afm="987654321", phone="69222")
    prop1 = Property(street="Πατησίων", number="124", area="Αθήνα", deiNumber="987654-01")
    lease1 = Lease(leaseId="00001", landlord=owner1, tenant=tenant1, end=date.today() + timedelta(days=5), amount=400.0, propertyObj=prop1)

    # Δεδομένα για το 2ο Συμβόλαιο (Λήγει σε 20 μέρες)
    owner2 = Customer(firstName="Κώστας", lastName="Αντωνίου", afm="111222333", phone="69333")
    tenant2 = Customer(firstName="Ελένη", lastName="Βασιλείου", afm="444555666", phone="69444")
    prop2 = Property(street="Τσιμισκή", number="40", area="Θεσσαλονίκη", deiNumber="111222-02")
    lease2 = Lease(leaseId="00002", landlord=owner2, tenant=tenant2, end=date.today() + timedelta(days=20), amount=550.0, propertyObj=prop2)

    # Αποθήκευση όλων στη βάση
    for obj in [owner1, tenant1, owner2, tenant2]: db.insert_customer(obj)
    db.insert_property(prop1)
    db.insert_property(prop2)
    db.insert_lease(lease1)
    db.insert_lease(lease2)

    # --- ΠΑΡΑΓΩΓΗ ΣΥΓΚΕΝΤΡΩΤΙΚΟΥ ΠΙΝΑΚΑ ---
    πίνακας_λήξεων = db.get_all_expiring_leases_summary(days_threshold=30)

    print("\n" + "="*110)
    print(f"{'ID':<7} | {'ΛΗΞΗ':<11} | {'ΗΜΕΡΕΣ':<6} | {'ΠΟΣΟ':<6} | {'ΕΚΜΙΣΘΩΤΗΣ (ΑΦΜ)':<25} | {'ΜΙΣΘΩΤΗΣ (ΑΦΜ)':<25} | {'ΑΚΙΝΗΤΟ'}")
    print("="*110)

    for r in πίνακας_λήξεων:
        landlord_info = f"{r['landlord_name']} ({r['landlord_afm']})"
        tenant_info = f"{r['tenant_name']} ({r['tenant_afm']})"

        print(f"{r['lease_id']:<7} | {r['end_date']:<11} | {r['days_left']:<6} | {r['amount']:<5}€ | {landlord_info:<25} | {tenant_info:<25} | {r['address']}")

    print("="*110 + "\n")

if __name__ == "__main__":
    test_summary_table()
