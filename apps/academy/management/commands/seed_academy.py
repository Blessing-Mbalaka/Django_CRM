from django.core.management.base import BaseCommand
from django.db import transaction

from apps.academy.models import Course, CourseModule, LearningPath


PATHS = [
    ('foundations', 'Entrepreneurship Foundations', 'foundations', [
        'Entrepreneurial Mindset', 'Identifying Business Opportunities', 'Idea Generation & Evaluation',
        'Problem–Solution Fit', 'Lean Canvas for SMEs', 'Business Models',
        'Starting & Formalising a Business in South Africa',
    ]),
    ('validation', 'Customer & Market Validation', 'validate', [
        'Understanding Your Customer', 'Customer Personas', 'Customer Discovery & Interviews',
        'Market Research for SMEs', 'Competitor Analysis', 'Testing Business Ideas',
        'Product–Market Fit', 'Pricing Your Product or Service',
    ]),
    ('finance', 'Financial Management', 'build', [
        'Financial Management for SMEs', 'Bookkeeping & Record Keeping', 'Cash-Flow Management',
        'Budgeting & Forecasting', 'Costing & Pricing', 'Profit, Revenue & Break-Even',
        'Separating Personal & Business Finances', 'Understanding Financial Statements',
    ]),
    ('marketing', 'Marketing & Sales', 'grow', [
        'Building an SME Brand', 'Digital Marketing', 'Social Media Marketing',
        'Creating Marketing Content', 'WhatsApp Business for SMEs', 'Customer Acquisition',
        'Sales Fundamentals', 'E-commerce & Selling Online', 'Customer Retention',
    ]),
    ('operations', 'Business Operations & Digitalisation', 'build', [
        'Running Efficient Business Operations', 'Inventory Management', 'Invoicing & Payments',
        'Customer Relationship Management', 'Project & Task Management', 'Digital Tools for SMEs',
        'Data for Business Decision-Making', 'AI for Small Businesses', 'Cybersecurity Basics',
    ]),
    ('compliance', 'South African Business & Compliance', 'build', [
        'Registering & Formalising Your Business', 'SARS & Tax Basics', 'CIPC Basics',
        'B-BBEE for SMEs', 'Employment & Labour Basics', 'POPIA & Customer Data',
        'Contracts for Small Businesses', 'Intellectual Property', 'Tender & Procurement Readiness',
    ]),
    ('funding', 'Funding & Investment Readiness', 'investment_ready', [
        'Understanding SME Funding in South Africa', 'Funding vs Loans vs Equity',
        'Becoming Funding Ready', 'Preparing Financial Documents', 'Business Plans for Funding',
        'Grant Applications', 'Pitch Deck Development', 'Pitching Your Business',
        'Investor Readiness', 'Business Valuation Basics',
    ]),
    ('growth', 'Growth & Scale', 'scale', [
        'Building a Growth Strategy', 'Scaling Operations', 'Building & Managing a Team',
        'Founder Leadership', 'Governance for Growing Businesses', 'Strategic Partnerships',
        'Enterprise Sales', 'Corporate Supplier Readiness', 'Export Readiness',
        'Innovation & Technology for Growth',
    ]),
]

OUTCOMES = {
    'foundations': ('Complete a one-page Lean Canvas', 'Describe the customer, problem, offer, costs and next assumption to test.'),
    'validation': ('Complete customer interviews', 'Write three open questions and record what the interviews reveal.'),
    'finance': ('Build a cash-flow forecast', 'List opening cash, expected receipts and payments for the next four weeks.'),
    'marketing': ('Create a marketing campaign', 'Choose an offer, audience, channel and measurable result.'),
    'operations': ('Improve one business process', 'Map the steps, name the owner and choose a small change to review.'),
    'compliance': ('Prepare a compliance questions checklist', 'List questions and find the relevant official authority.'),
    'funding': ('Prepare a funding pack', 'Describe the funding need and list the available documents and evidence.'),
    'growth': ('Create a practical growth plan', 'Choose a goal, identify a constraint and set a team review date.'),
}

MODULE_TITLES = [
    'Getting Started',
    'Understanding the Business Need',
    'Practical Example',
    'Guided Activity',
    'Review Your Approach',
    'Test Your Learning',
    'Apply It to Your Business',
    'Additional Resources',
    'Reflect & Discuss',
]


def module_defaults(course, position, outcome, action):
    title = MODULE_TITLES[position]
    common = {'title': title, 'position': position, 'is_published': True}
    if position == 0 and course.slug == 'idea':
        return {
            **common,
            'module_type': CourseModule.Type.VIDEO,
            'body': course.description,
            'video_url': 'https://www.youtube.com/watch?v=M7lc1UVf-VE',
        }
    if position == 3:
        return {
            **common,
            'module_type': CourseModule.Type.ACTIVITY,
            'body': 'Apply the lesson to one current business question.',
            'prompt': 'What will you investigate or test next?',
        }
    if position == 5:
        return {
            **common,
            'module_type': CourseModule.Type.QUIZ,
            'prompt': 'Which is the most useful next step after this course?',
            'quiz_options': [
                outcome,
                'Wait until every detail is certain',
                'Copy another business without checking',
                'Make a large commitment without evidence',
            ],
            'correct_option': 0,
        }
    if position == 6:
        return {
            **common,
            'module_type': CourseModule.Type.PRACTICAL,
            'body': action,
            'prompt': outcome,
        }
    if position == 7:
        return {
            **common,
            'module_type': CourseModule.Type.RESOURCE,
            'body': 'Use a relevant worksheet or business tool to organise your next steps.',
        }
    if position == 8:
        return {
            **common,
            'module_type': CourseModule.Type.REFLECTION,
            'prompt': 'What will you do differently in your business?',
        }
    return {
        **common,
        'module_type': CourseModule.Type.ARTICLE,
        'body': (
            f'{course.title} helps an SME owner make a practical, evidence-based decision. '
            f'Work towards this outcome: {outcome}. {action}'
        ),
    }


class Command(BaseCommand):
    help = 'Seed the editable SME Academy sample catalogue without overwriting administrator changes.'

    @transaction.atomic
    def handle(self, *args, **options):
        created_paths = 0
        created_courses = 0
        created_modules = 0

        path_records = {}
        for path_position, (slug, title, stage, course_titles) in enumerate(PATHS):
            path, created = LearningPath.objects.get_or_create(
                slug=slug,
                defaults={
                    'title': title,
                    'description': f'Practical courses for the {title.lower()} learning path.',
                    'business_stage': stage,
                    'position': path_position,
                    'is_published': True,
                },
            )
            created_paths += int(created)
            path_records[slug] = path

            outcome, action = OUTCOMES[slug]
            for course_position, course_title in enumerate(course_titles):
                course, course_created = Course.objects.get_or_create(
                    slug=f'{slug}-{course_position}',
                    defaults={
                        'path': path,
                        'title': course_title,
                        'description': f'Build practical skills in {course_title.lower()} and leave with a next step for your business.',
                        'learning_outcome': outcome,
                        'instructor_name': 'Academy facilitator',
                        'level': Course.Level.INTERMEDIATE if slug == 'growth' else Course.Level.BEGINNER,
                        'duration_minutes': 45 + course_position % 4 * 15,
                        'position': course_position,
                        'is_published': True,
                    },
                )
                created_courses += int(course_created)
                for module_position in range(len(MODULE_TITLES)):
                    _, module_created = CourseModule.objects.get_or_create(
                        course=course,
                        position=module_position,
                        defaults=module_defaults(course, module_position, outcome, action),
                    )
                    created_modules += int(module_created)

        extra_courses = [
            {
                'slug': 'idea',
                'path': path_records['foundations'],
                'title': 'Idea Generation for South African SMEs',
                'description': 'Explore useful business ideas and choose one customer problem to investigate.',
                'learning_outcome': 'Evaluate a business idea',
                'instructor_name': 'Academy facilitator',
                'level': Course.Level.BEGINNER,
                'duration_minutes': 75,
                'position': len(PATHS[0][3]),
                'is_published': True,
            },
            {
                'slug': 'discovery',
                'path': path_records['validation'],
                'title': 'Customer Discovery & Market Validation',
                'description': 'Plan customer conversations and use evidence to validate a market need.',
                'learning_outcome': 'Complete customer interviews',
                'instructor_name': 'Academy facilitator',
                'level': Course.Level.BEGINNER,
                'duration_minutes': 75,
                'position': len(PATHS[1][3]),
                'is_published': True,
            },
        ]
        for defaults in extra_courses:
            slug = defaults.pop('slug')
            course, course_created = Course.objects.get_or_create(slug=slug, defaults=defaults)
            created_courses += int(course_created)
            path_slug = course.path.slug
            outcome, action = OUTCOMES[path_slug]
            for module_position in range(len(MODULE_TITLES)):
                _, module_created = CourseModule.objects.get_or_create(
                    course=course,
                    position=module_position,
                    defaults=module_defaults(course, module_position, outcome, action),
                )
                created_modules += int(module_created)

        self.stdout.write(self.style.SUCCESS(
            f'Academy seed complete: {created_paths} paths, {created_courses} courses, '
            f'{created_modules} modules created.'
        ))
