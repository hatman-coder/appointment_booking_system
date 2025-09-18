# apps/locations/management/commands/seed_locations.py
from django.core.management.base import BaseCommand
from apps.location.models import Division, District, Thana


class Command(BaseCommand):
    help = "Seed database with Bangladesh divisions, districts, and thanas"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Bangladesh locations...")

        # Clear existing data
        Thana.objects.all().delete()
        District.objects.all().delete()
        Division.objects.all().delete()

        # Create divisions, districts, and thanas
        self.create_dhaka_division()
        self.create_chittagong_division()
        self.create_rajshahi_division()
        self.create_khulna_division()
        self.create_barisal_division()
        self.create_sylhet_division()
        self.create_rangpur_division()
        self.create_mymensingh_division()

        self.stdout.write(self.style.SUCCESS("Successfully seeded locations!"))
        self.stdout.write(f"Created {Division.objects.count()} divisions")
        self.stdout.write(f"Created {District.objects.count()} districts")
        self.stdout.write(f"Created {Thana.objects.count()} thanas")

    def create_dhaka_division(self):
        # Dhaka Division
        dhaka_div = Division.objects.create(name="Dhaka", code="10")

        # Dhaka District
        dhaka_dist = District.objects.create(
            name="Dhaka", code="26", division=dhaka_div
        )
        dhaka_thanas = [
            "Dhanmondi",
            "Wari",
            "Tejgaon",
            "Gulshan",
            "Motijheel",
            "Ramna",
            "Pallabi",
            "Shah Ali",
            "Adabor",
            "Kafrul",
            "Uttara East",
            "Uttara West",
            "Mirpur Model",
            "Pallabi",
            "Sher-e-Bangla Nagar",
            "New Market",
            "Kotwali",
            "Sutrapur",
            "Hazaribagh",
            "Lalbagh",
        ]
        for i, thana in enumerate(dhaka_thanas, 1):
            Thana.objects.create(name=thana, code=f"2601{i:02d}", district=dhaka_dist)

        # Gazipur District
        gazipur_dist = District.objects.create(
            name="Gazipur", code="33", division=dhaka_div
        )
        gazipur_thanas = [
            "Gazipur Sadar",
            "Kaliakair",
            "Kaliganj",
            "Kapasia",
            "Sreepur",
        ]
        for i, thana in enumerate(gazipur_thanas, 1):
            Thana.objects.create(name=thana, code=f"3301{i:02d}", district=gazipur_dist)

        # Narayanganj District
        narayanganj_dist = District.objects.create(
            name="Narayanganj", code="67", division=dhaka_div
        )
        narayanganj_thanas = [
            "Narayanganj Sadar",
            "Bandar",
            "Fatullah",
            "Siddhirganj",
            "Sonargaon",
            "Araihazar",
        ]
        for i, thana in enumerate(narayanganj_thanas, 1):
            Thana.objects.create(
                name=thana, code=f"6701{i:02d}", district=narayanganj_dist
            )

        # Tangail District
        tangail_dist = District.objects.create(
            name="Tangail", code="92", division=dhaka_div
        )
        tangail_thanas = [
            "Tangail Sadar",
            "Mirzapur",
            "Gopalpur",
            "Basail",
            "Sakhipur",
            "Delduar",
            "Ghatail",
            "Kalihati",
        ]
        for i, thana in enumerate(tangail_thanas, 1):
            Thana.objects.create(name=thana, code=f"9201{i:02d}", district=tangail_dist)

    def create_chittagong_division(self):
        # Chittagong Division
        chittagong_div = Division.objects.create(name="Chittagong", code="20")

        # Chittagong District
        chittagong_dist = District.objects.create(
            name="Chittagong", code="15", division=chittagong_div
        )
        chittagong_thanas = [
            "Kotwali",
            "Panchlaish",
            "Double Mooring",
            "Halishahar",
            "Khulshi",
            "Chandgaon",
            "Karnaphuli",
            "Banshkhali",
            "Boalkhali",
            "Anwara", 
            "Chandanaish",
            "Satkania",
            "Lohagara",
            "Fatikchhari",
            "Raozan",
            "Rangunia",
            "Sitakunda",
            "Mirsharai",
            "Patiya",
            "Sandwip",
            "Hatiya",
            "Feni Sadar",
            "Noakhali Sadar"
            # Add more thanas here
        ]
        for i, thana in enumerate(chittagong_thanas, 1):
            Thana.objects.create(
                name=thana, code=f"1501{i:02d}", district=chittagong_dist
            )

        # Cox's Bazar District
        coxsbazar_dist = District.objects.create(
            name="Cox's Bazar", code="22", division=chittagong_div
        )
        coxsbazar_thanas = [
            "Cox's Bazar Sadar",
            "Chakaria",
            "Teknaf",
            "Ukhia",
            "Maheshkhali",
            "Pekua",
            "Ramu",
            "Kutubdia",
        ]
        for i, thana in enumerate(coxsbazar_thanas, 1):
            Thana.objects.create(
                name=thana, code=f"2201{i:02d}", district=coxsbazar_dist
            )

    def create_rajshahi_division(self):
        # Rajshahi Division
        rajshahi_div = Division.objects.create(name="Rajshahi", code="80")

        # Rajshahi District
        rajshahi_dist = District.objects.create(
            name="Rajshahi", code="81", division=rajshahi_div
        )
        rajshahi_thanas = [
            "Boalia",
            "Motihar",
            "Rajpara",
            "Shah Makhdum",
            "Paba",
            "Durgapur",
            "Mohonpur",
            "Charghat",
            "Puthia",
            "Bagha",
            "Godagari",
            "Tanore",
        ]
        for i, thana in enumerate(rajshahi_thanas, 1):
            Thana.objects.create(
                name=thana, code=f"8101{i:02d}", district=rajshahi_dist
            )

        # Bogra District
        bogra_dist = District.objects.create(
            name="Bogra", code="05", division=rajshahi_div
        )
        bogra_thanas = [
            "Bogra Sadar",
            "Adamdighi",
            "Dhunat",
            "Dhupchanchia",
            "Gabtali",
            "Kahaloo",
            "Nandigram",
            "Sariakandi",
            "Shajahanpur",
            "Sherpur",
            "Shibganj",
            "Sonatola",
        ]
        for i, thana in enumerate(bogra_thanas, 1):
            Thana.objects.create(name=thana, code=f"0501{i:02d}", district=bogra_dist)

    def create_khulna_division(self):
        # Khulna Division
        khulna_div = Division.objects.create(name="Khulna", code="40")

        # Khulna District
        khulna_dist = District.objects.create(
            name="Khulna", code="47", division=khulna_div
        )
        khulna_thanas = [
            "Kotwali",
            "Sonadanga",
            "Khalishpur",
            "Daulatpur",
            "Khan Jahan Ali",
            "Harintana",
            "Batiaghata",
            "Dacope",
            "Dumuria",
            "Dighalia",
            "Koyra",
            "Paikgachha",
            "Phultala",
            "Rupsa",
            "Terokhada",
        ]
        for i, thana in enumerate(khulna_thanas, 1):
            Thana.objects.create(name=thana, code=f"4701{i:02d}", district=khulna_dist)

        # Jessore District
        jessore_dist = District.objects.create(
            name="Jessore", code="41", division=khulna_div
        )
        jessore_thanas = [
            "Jessore Sadar",
            "Abhaynagar",
            "Bagherpara",
            "Chaugachha",
            "Jhikargachha",
            "Keshabpur",
            "Manirampur",
            "Sharsha",
        ]
        for i, thana in enumerate(jessore_thanas, 1):
            Thana.objects.create(name=thana, code=f"4101{i:02d}", district=jessore_dist)

    def create_barisal_division(self):
        # Barisal Division
        barisal_div = Division.objects.create(name="Barisal", code="50")

        # Barisal District
        barisal_dist = District.objects.create(
            name="Barisal", code="06", division=barisal_div
        )
        barisal_thanas = [
            "Kotwali",
            "Bakerganj",
            "Babuganj",
            "Wazirpur",
            "Banaripara",
            "Gournadi",
            "Agailjhara",
            "Mehendiganj",
            "Muladi",
            "Hizla",
        ]
        for i, thana in enumerate(barisal_thanas, 1):
            Thana.objects.create(name=thana, code=f"0601{i:02d}", district=barisal_dist)

        # Patuakhali District
        patuakhali_dist = District.objects.create(
            name="Patuakhali", code="76", division=barisal_div
        )
        patuakhali_thanas = [
            "Patuakhali Sadar",
            "Bauphal",
            "Dashmina",
            "Galachipa",
            "Kalapara",
            "Mirzaganj",
            "Rangabali",
            "Dumki",
        ]
        for i, thana in enumerate(patuakhali_thanas, 1):
            Thana.objects.create(
                name=thana, code=f"7601{i:02d}", district=patuakhali_dist
            )

    def create_sylhet_division(self):
        # Sylhet Division
        sylhet_div = Division.objects.create(name="Sylhet", code="60")

        # Sylhet District
        sylhet_dist = District.objects.create(
            name="Sylhet", code="87", division=sylhet_div
        )
        sylhet_thanas = [
            "Kotwali",
            "Jalalabad",
            "Dakshin Surma",
            "Shah Poran",
            "Osmani Nagar",
            "Balaganj",
            "Beanibazar",
            "Bishwanath",
            "Companiganj",
            "Fenchuganj",
            "Golapganj",
            "Gowainghat",
            "Jointiapur",
            "Kanaighat",
            "Sylhet Sadar",
            "Zakiganj",
        ]
        for i, thana in enumerate(sylhet_thanas, 1):
            Thana.objects.create(name=thana, code=f"8701{i:02d}", district=sylhet_dist)

    def create_rangpur_division(self):
        # Rangpur Division
        rangpur_div = Division.objects.create(name="Rangpur", code="55")

        # Rangpur District
        rangpur_dist = District.objects.create(
            name="Rangpur", code="85", division=rangpur_div
        )
        rangpur_thanas = [
            "Kotwali",
            "Rangpur Sadar",
            "Badarganj",
            "Gangachara",
            "Kaunia",
            "Mithapukur",
            "Pirgachha",
            "Pirganj",
            "Taraganj",
        ]
        for i, thana in enumerate(rangpur_thanas, 1):
            Thana.objects.create(name=thana, code=f"8501{i:02d}", district=rangpur_dist)

        # Dinajpur District
        dinajpur_dist = District.objects.create(
            name="Dinajpur", code="30", division=rangpur_div
        )
        dinajpur_thanas = [
            "Dinajpur Sadar",
            "Birampur",
            "Birganj",
            "Biral",
            "Bochaganj",
            "Chirirbandar",
            "Phulbari",
            "Ghoraghat",
            "Hakimpur",
            "Kaharole",
            "Khansama",
            "Nawabganj",
            "Parbatipur",
        ]
        for i, thana in enumerate(dinajpur_thanas, 1):
            Thana.objects.create(
                name=thana, code=f"3001{i:02d}", district=dinajpur_dist
            )

    def create_mymensingh_division(self):
        # Mymensingh Division
        mymensingh_div = Division.objects.create(name="Mymensingh", code="70")

        # Mymensingh District
        mymensingh_dist = District.objects.create(
            name="Mymensingh", code="61", division=mymensingh_div
        )
        mymensingh_thanas = [
            "Kotwali",
            "Mymensingh Sadar",
            "Muktagachha",
            "Fulbaria",
            "Gaffargaon",
            "Gouripur",
            "Haluaghat",
            "Ishwarganj",
            "Nandail",
            "Phulpur",
            "Bhaluka",
            "Trishal",
        ]
        for i, thana in enumerate(mymensingh_thanas, 1):
            Thana.objects.create(
                name=thana, code=f"6101{i:02d}", district=mymensingh_dist
            )
