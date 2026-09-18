"""
Management command: seed_users
Creates dummy departments and users for development/demo purposes.
Usage: python manage.py seed_users
       python manage.py seed_users --clear   (wipe non-superuser accounts first)
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User
from apps.centres.models import Centre
from apps.accounts.demo import DEFAULT_DEMO_PASSWORD

CENTRES = [
    {'name': 'Centre for Entrepreneurship & Innovation',        'code': 'CEI'},
    {'name': 'Centre for Leadership & Organisational Change',   'code': 'CLOC'},
    {'name': 'Centre for Applied Management Research',          'code': 'CAMR'},
    {'name': 'Centre for Sustainability & Governance',          'code': 'CSG'},
]

# (first_name, last_name, email, username, role, job_title, phone, centre_code)
USERS = [
    # ── CEO ──
    ('Nomsa',    'Dlamini',  'n.dlamini@uj.ac.za',   'ndlamini',  User.Role.CEO,      'CEO: JBS',                         '+27 11 559 3001', None),

    # ── Directors ──
    ('Sipho',    'Nkosi',    's.nkosi@uj.ac.za',     'snkosi',    User.Role.DIRECTOR, 'Director: CEI',                    '+27 11 559 3101', 'CEI'),
    ('Fatima',   'Essop',    'f.essop@uj.ac.za',     'fessop',    User.Role.DIRECTOR, 'Director: CLOC',                   '+27 11 559 3102', 'CLOC'),
    ('Johan',    'Pretorius','j.pretorius@uj.ac.za', 'jpretorius',User.Role.DIRECTOR, 'Director: CAMR',                   '+27 11 559 3103', 'CAMR'),
    ('Lindiwe',  'Mokoena',  'l.mokoena@uj.ac.za',   'lmokoena',  User.Role.DIRECTOR, 'Director: CSG',                    '+27 11 559 3104', 'CSG'),

    # ── Engagement Leads ──
    ('Kagiso',   'Sithole',  'k.sithole@uj.ac.za',   'ksithole',  User.Role.LEAD,     'Engagement Lead',                  '+27 11 559 3201', 'CEI'),
    ('Priya',    'Naidoo',   'p.naidoo@uj.ac.za',    'pnaidoo',   User.Role.LEAD,     'Engagement Lead',                  '+27 11 559 3202', 'CLOC'),
    ('Andile',   'Zulu',     'a.zulu@uj.ac.za',      'azulu',     User.Role.LEAD,     'Engagement Lead',                  '+27 11 559 3203', 'CAMR'),
    ('Thandeka', 'Khoza',    't.khoza@uj.ac.za',     'tkhoza',    User.Role.LEAD,     'Engagement Lead',                  '+27 11 559 3204', 'CSG'),

    # ── Analysts ──
    ('Ruan',     'van Wyk',  'r.vanwyk@uj.ac.za',    'rvanwyk',   User.Role.ANALYST,  'Research Analyst',                 '+27 11 559 3301', 'CEI'),
    ('Amahle',   'Buthelezi','a.buthelezi@uj.ac.za', 'abuthelezi',User.Role.ANALYST,  'Data Analyst',                     '+27 11 559 3302', 'CAMR'),
    ('Yusuf',    'Hendricks','y.hendricks@uj.ac.za', 'yhendricks',User.Role.ANALYST,  'Financial Analyst',                '+27 11 559 3303', 'CSG'),

    # ── General Staff ──
    ('Zanele',   'Mahlangu', 'z.mahlangu@uj.ac.za',  'zmahlangu', User.Role.STAFF,    'Programme Coordinator',            '+27 11 559 3401', 'CEI'),
    ('Pieter',   'Botha',    'p.botha@uj.ac.za',     'pbotha',    User.Role.STAFF,    'Events & Logistics Officer',       '+27 11 559 3402', 'CLOC'),
    ('Nokukhanya','Ntuli',   'n.ntuli@uj.ac.za',     'nntuli',    User.Role.STAFF,    'Client Relations Officer',         '+27 11 559 3403', 'CAMR'),
    ('Deon',     'Joubert',  'd.joubert@uj.ac.za',   'djoubert',  User.Role.STAFF,    'Communications Officer',           '+27 11 559 3404', 'CSG'),

    # ── System Admin ──
    ('Mpho',     'Radebe',   'm.radebe@uj.ac.za',    'mradebe',   User.Role.ADMIN,    'CRM System Administrator',         '+27 11 559 3501', None),
]

class Command(BaseCommand):
    help = 'Seed dummy departments and users for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all non-superuser accounts before seeding',
        )
        parser.add_argument(
            '--reset-demo-passwords',
            action='store_true',
            help='Restore the documented development password on seeded demo accounts.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['clear']:
            deleted, _ = User.objects.filter(is_superuser=False).delete()
            Centre.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Cleared {deleted} existing user(s) and all departments.'))

        # ── Create departments ──────────────────────────────────────────────
        centre_map = {}
        for c in CENTRES:
            obj, created = Centre.objects.get_or_create(
                code=c['code'],
                defaults={'name': c['name'], 'is_active': True},
            )
            centre_map[c['code']] = obj
            status = 'created' if created else 'exists '
            self.stdout.write(f'  [{status}] Department: {obj.name}')

        # ── Create users ────────────────────────────────────────────────────
        created_count = 0
        reset_count = 0
        for first, last, email, uname, role, title, phone, centre_code in USERS:
            existing = User.objects.filter(username=uname).first()
            if existing:
                if options['reset_demo_passwords']:
                    existing.set_password(DEFAULT_DEMO_PASSWORD)
                    existing.is_active = True
                    existing.save(update_fields=['password', 'is_active'])
                    reset_count += 1
                self.stdout.write(f'  [exists ] User: {uname}')
                continue

            centre = centre_map.get(centre_code) if centre_code else None
            user = User.objects.create_user(
                username=uname,
                email=email,
                password=DEFAULT_DEMO_PASSWORD,
                first_name=first,
                last_name=last,
                role=role,
                job_title=title,
                phone=phone,
                centre=centre,
            )
            created_count += 1
            self.stdout.write(f'  [created] User: {user.get_full_name():<25} role={role:<10} -> {uname}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {created_count} user(s) created, {reset_count} password(s) reset. '
            f'Password for all: {DEFAULT_DEMO_PASSWORD}'
        ))
