"""
This module contains all the questions used in the resume generation process.
These are hardcoded since we're not using a database.
"""

# Personal information questions (should be asked first)
PERSONAL_INFO_QUESTIONS = [
    {
        "text": {
            "uz": "Ismingiz va familiyangiz (sharif) nima?",
            "ru": "Как ваше имя и фамилия?",
            "en": "What is your first name and last name (surname)?",
        },
        "category": "personal",
        "field_name": "full_name",
        "is_required": True,
        "order": 1,
    },
    {
        "text": {
            "uz": "Elektron pochta manzilingiz nima?",
            "ru": "Какой у вас адрес электронной почты?",
            "en": "What is your email address?",
        },
        "category": "personal",
        "field_name": "email",
        "is_required": True,
        "order": 2,
    },
    {
        "text": {
            "uz": "Telefon raqamingiz nima?",
            "ru": "Какой у вас номер телефона?",
            "en": "What is your phone number?",
        },
        "category": "personal",
        "field_name": "phone",
        "is_required": False,
        "order": 3,
    },
    {
        "text": {
            "uz": "Qaysi mamlakat va shaharda yashaysiz?",
            "ru": "В какой стране и городе вы находитесь?",
            "en": "Which country and city do you live in?",
        },
        "category": "personal",
        "field_name": "location",
        "is_required": False,
        "order": 4,
    },
    {
        "text": {
            "uz": "Ijtimoiy tarmoq profillaringiz bormi? (LinkedIn, GitHub, Telegram, va h.k.)\n\nHavolalarni kiriting.",
            "ru": "Есть ли у вас профили в соцсетях? (LinkedIn, GitHub, Telegram и т.д.)\n\nУкажите ссылки.",
            "en": "Do you have any social media profiles? (LinkedIn, GitHub, Telegram, etc.)\n\nInclude links.",
        },
        "category": "personal",
        "field_name": "social_links",
        "is_required": False,
        "order": 5,
    },
]

# Generic questions for all users
GENERIC_QUESTIONS = [
    {
        "text": {
            "en": "Please provide a professional summary about yourself, highlighting your key skills and career goals.",
            "ru": "Пожалуйста, предоставьте профессиональное резюме о себе, выделив ключевые навыки и карьерные цели.",
            "uz": "Iltimos, o'zingiz haqingizda professional qisqacha ma'lumot bering, asosiy ko'nikmalaringiz va kariyerangiz maqsadlarini ta'kidlab o'ting.",
        },
        "category": "professional",
        "field_name": "summary",
        "is_required": True,
        "order": 6,
    },
    {
        "text": {
            "en": "Describe your work experience. For each job, include your position, company, dates, main responsibilities, and tools or methods used.",
            "ru": "Опишите ваш опыт работы. Для каждой должности укажите вашу позицию, компанию, даты, основные обязанности и используемые инструменты или методы.",
            "uz": "Ish tajribangizni tasvirlab bering. Har bir ish uchun lavozimingiz, kompaniya, sanalar, asosiy vazifalar va ishlatilgan vositalar yoki uslublarni kiriting.",
        },
        "category": "professional",
        "field_name": "experiences",
        "is_required": True,
        "order": 7,
    },
    {
        "text": {
            "en": "What are some achievements or results you're proud of in your roles?\n\nInclude measurable outcomes if possible.",
            "ru": "Какие достижения или результаты вы гордитесь в своих ролях?\n\nВключите измеримые результаты, если возможно.",
            "uz": "Ishlaringizda qanday yaxshi natijalarga erishgansiz?\n\nAgar mumkin bo'lsa, o'lchovli natijalarni ham kiriting.",
        },
        "category": "professional",
        "field_name": "achievements",
        "is_required": False,
        "order": 8,
    },
    {
        "text": {
            "en": "List your technical skills and professional abilities relevant to your work.\n\nGroup them by category if possible (e.g., tools, methods, languages, soft skills) and briefly mention how you've applied each one in your work.",
            "ru": "Перечислите ваши технические навыки и профессиональные способности, относящиеся к вашей работе.\n\nПо возможности сгруппируйте их по категориям (например, инструменты, методы, языки, мягкие навыки) и кратко укажите, как вы применяли каждый из них в работе.",
            "uz": "Ishingizga tegishli texnik ko'nikmalaringiz va professional qobiliyatlaringizni sanab o'ting.\n\nIloji bo'lsa, ularni toifalar bo'yicha guruhlang (masalan, vositalar, usullar, tillar, ijtimoiy ko'nikmalar) va har birini ishda qanday qo'llaganingizni qisqacha ko'rsating.",
        },
        "category": "skills",
        "field_name": "skills",
        "is_required": True,
        "order": 9,
    },
    {
        "text": {
            "en": "Tell us about your education. Include degrees, institutions, graduation dates, and any notable projects or honors.",
            "ru": "Расскажите нам о вашем образовании. Включите степени, учебные заведения, даты окончания и любые заметные проекты или награды.",
            "uz": "Ta'limingiz haqida gapiring. Darajalar, muassasalar, bitiruv sanalari va har qanday muhim loyihalar yoki mukofotlarni kiriting.",
        },
        "category": "education",
        "field_name": "education",
        "is_required": True,
        "order": 10,
    },
    {
        "text": {
            "en": "Have you completed any professional certifications, courses, or special training relevant to your work?\n\nProvide details.",
            "ru": "Завершили ли вы какие-либо профессиональные сертификаты, курсы или специальное обучение, относящиеся к вашей работе?\n\nПредоставьте детали.",
            "uz": "Ishingizga tegishli bo'lgan har qanday professional sertifikatlar, kurslar yoki maxsus treninglarni tugatdingizmi?\n\nTafsilotlarni taqdim eting.",
        },
        "category": "certifications",
        "field_name": "certifications",
        "is_required": False,
        "order": 11,
    },
    {
        "text": {
            "en": "Are you a member of any professional organizations, associations, or communities?\n\nFor each one, include the name, your role or membership type, how long you've been involved, and any contributions you've made (e.g., speaker, organizer, mentor).",
            "ru": "Являетесь ли вы членом каких-либо профессиональных организаций, ассоциаций или сообществ?\n\nДля каждой укажите название, вашу роль или тип членства, как долго вы участвуете, и любой вклад, который вы внесли (например, докладчик, организатор, наставник).",
            "uz": "Biror bir professional tashkilot, assotsiatsiya yoki jamoaning a'zosimisiz?\n\nHar biri uchun nomini, rolingizni yoki a'zolik turini, qancha vaqtdan beri qatnashayotganingizni va qilgan hissangizni ko'rsating (masalan, ma'ruzachi, tashkilotchi, mentor).",
        },
        "category": "professional",
        "field_name": "affiliations",
        "is_required": False,
        "order": 12,
    },
    {
        "text": {
            "en": "Have you worked on any significant projects?\n\nDescribe the project, your role, duration, methods or tools used, and results. Include links if possible.",
            "ru": "Работали ли вы над какими-либо значительными проектами?\n\nОпишите проект, вашу роль, продолжительность, методы или инструменты, которые вы использовали, и результаты. Включите ссылки, если возможно.",
            "uz": "Muhim loyihalarda ishlaganmisiz?\n\nLoyihani, o'z rolingizni, davomiyligini, ishlatilgan usullar yoki vositalarni va natijalarni tasvirlab bering. Agar mumkin bo'lsa, havolalarni kiritib o'ting.",
        },
        "category": "projects",
        "field_name": "projects",
        "is_required": False,
        "order": 13,
    },
    {
        "text": {
            "en": "Do you have any volunteer or side work experience you'd like to include?\n\nFor each role, describe the organization, your position, duration, main responsibilities, tools or methods used, and any measurable outcomes or impact.",
            "ru": "Есть ли у вас опыт волонтерской или побочной работы, который вы хотели бы включить?\n\nДля каждой роли опишите организацию, вашу должность, продолжительность, основные обязанности, используемые инструменты или методы, а также любые измеримые результаты или влияние.",
            "uz": "Qo'shimcha yoki ko'ngilli ish tajribangiz bormi?\n\nHar bir rol uchun tashkilotni, lavozimingizni, davomiyligini, asosiy vazifalaringizni, ishlatilgan vositalar yoki usullarni va o'lchovli natijalar yoki ta'sirni tasvirlab bering.",
        },
        "category": "volunteer",
        "field_name": "volunteer_experience",
        "is_required": False,
        "order": 14,
    },
]


# Position-specific questions
POSITION_QUESTIONS = {}
