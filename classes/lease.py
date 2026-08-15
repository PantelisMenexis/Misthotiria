import datetime 
from classes.customer import Customer
from classes.property import Property

class Lease:
    leaseId: str
    leaseType: str
    start: datetime.date
    end: datetime.date
    amount: float
    notes: str
    landlords: list    # Λίστα από αντικείμενα Customer
    tenants: list      # Λίστα από αντικείμενα Customer
    properties: list   # <--- ΑΛΛΑΓΗ: Λίστα από αντικείμενα Property

    def __init__(self, leaseId="", leaseType="", start=None, end=None, amount=0.0, notes="", landlords=None, tenants=None, properties=None):
        self.leaseId = leaseId
        self.leaseType = leaseType
        self.start = start
        self.end = end
        self.amount = amount
        self.notes = notes
        self.landlords = landlords if landlords is not None else []
        self.tenants = tenants if tenants is not None else []
        self.properties = properties if properties is not None else [] # Αρχικοποίηση λίστας
