from apps.accounts.models import User

# List of test users and their roles
users = [
    ("ndlamini", "Nomsa", "Dlamini", "dean"),
    ("mradebe", "Mpho", "Radebe", "admin"),
    ("snkosi", "Sipho", "Nkosi", "director"),
    ("fessop", "Fatima", "Essop", "director"),
    ("jpretorius", "Johan", "Pretorius", "director"),
    ("lmokoena", "Lindiwe", "Mokoena", "director"),
    ("ksithole", "Kagiso", "Sithole", "lead"),
    ("pnaidoo", "Priya", "Naidoo", "lead"),
    ("azulu", "Andile", "Zulu", "lead"),
    ("tkhoza", "Thandeka", "Khoza", "lead"),
    ("rvanwyk", "Ruan", "van Wyk", "analyst"),
    ("abuthelezi", "Amahle", "Buthelezi", "analyst"),
    ("yhendricks", "Yusuf", "Hendricks", "analyst"),
    ("zmahlangu", "Zanele", "Mahlangu", "staff"),
    ("pbotha", "Pieter", "Botha", "staff"),
    ("nntuli", "Nokukhanya", "Ntuli", "staff"),
    ("djoubert", "Deon", "Joubert", "staff"),
]

for username, first, last, role in users:
    exists = User.objects.filter(username=username).exists()
    print(f"{username}: {'EXISTS' if exists else 'MISSING'} (role: {role})")
