class Customer:
    afm: str
    firstName: str
    lastName: str
    fatherName: str
    motherName: str
    phone: str
    isActive: int  # <--- ΝΕΟ ΠΕΔΙΟ (1 = Ενεργός, 0 = Ανενεργός)

    def __init__(self, afm="", firstName="", lastName="", fatherName="", motherName="", phone="", isActive=1):
        self.afm = afm
        self.firstName = firstName
        self.lastName = lastName
        self.fatherName = fatherName
        self.motherName = motherName
        self.phone = phone
        self.isActive = isActive

