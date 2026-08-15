class Property:
    propertyId: int
    leaseId: int  # <--- Σύνδεση με το συμβόλαιο
    aa: int       # <--- ΝΕΟ ΠΕΔΙΟ: Α/Α ακινήτου στο συμβόλαιο
    street: str
    number: str
    area: str
    postalCode: str
    propertyType: str
    floor: str
    squareMeters: float
    deiNumber: str
    atak: str
    sub_amount: float  # <--- ΝΕΟ ΠΕΔΙΟ: Επιμέρους Μίσθωμα

    def __init__(self, propertyId=None, leaseId=None, aa=1, street="", number="", area="", postalCode="",
                 propertyType="", floor="", squareMeters=0.0, deiNumber="", atak="", sub_amount=0.0):
        self.propertyId = propertyId
        self.leaseId = leaseId
        self.aa = aa
        self.street = street
        self.number = number
        self.area = area
        self.postalCode = postalCode
        self.propertyType = propertyType
        self.floor = floor
        self.squareMeters = squareMeters
        self.deiNumber = deiNumber
        self.atak = atak
        self.sub_amount = sub_amount
