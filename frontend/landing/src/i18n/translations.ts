export type Locale = "uz" | "ru" | "en";

const translations = {
  uz: {
    nav: {
      features: "Imkoniyatlar",
      howItWorks: "Qanday ishlaydi",
      pricing: "Narxlar",
      about: "Biz haqimizda",
      tryFree: "Bepul sinash",
    },
    hero: {
      titlePre: "Sizning",
      titleGradient: "AI karyera",
      titlePost: "agentingiz",
      subtitle:
        "Yaxshiroq rezyume yarating. Yaxshiroq ish toping. Intervyularni muvaffaqiyatli o\u2018ting \u2014",
      subtitleHighlight: "hammasi chatda.",
      subtitleEnd: "Telegramdagi AI karyera yordamchingiz.",
      cta: "Telegramda boshlash",
      learnMore: "Batafsil",
      statFreeValue: "Bepul",
      statFreeLabel: "Boshlash uchun",
      statLangValue: "4",
      statLangLabel: "Tillar",
      statAiValue: "AI",
      statAiLabel: "Texnologiya",
    },
    features: {
      label: "Biz nima qilamiz",
      title: "Keyingi lavozimingiz uchun",
      titleGradient: "kerak bo\u2018lgan hamma narsa",
      resumeTitle: "AI rezyume yaratuvchi",
      resumeDesc:
        "Rezyumengizni yuklang yoki savollarga javob bering \u2014 AI kuchli tomonlaringizni ta\u2018kidlaydigan professional rezyume yaratadi.",
      jobTitle: "Aqlli ish moslash",
      jobDesc:
        "Biz vakansiyalarni saytlar, kompaniya sahifalari va Telegram kanallaridan to\u2018playmiz \u2014 keyin AI yordamida ko\u2018nikmalaringizga moslashtiramiz.",
      interviewTitle: "Intervyuga tayyorgarlik",
      interviewDesc:
        "Maqsadli lavozimingizga moslashtirilgan AI savollar bilan mashq qiling. Ball oling, fikr-mulohaza oling, yaxshilaning.",
    },
    howItWorks: {
      label: "Oddiy jarayon",
      title: "Qanday",
      titleGradient: "ishlaydi",
      step1Title: "Botni ishga tushiring",
      step1Desc:
        "Telegramda @SiviAIBot ni oching va Start bosing. Ro\u2018yxatdan o\u2018tish shart emas.",
      step2Title: "Rezyumengizni yarating",
      step2Desc:
        "Mavjud rezyumeni yuklang yoki savollarga javob bering. Qolganini AI qiladi.",
      step3Title: "Ish toping",
      step3Desc:
        "AI minglab vakansiyalarni ko\u2018rib chiqadi va profilingizga mos keladiganlarini topadi.",
      step4Title: "Intervyuni yutib chiqing",
      step4Desc:
        "Moslashtirilgan savollar bilan mashq qiling va yaxshilanish uchun foydali fikr-mulohaza oling.",
    },
    video: {
      label: "Amalda ko\u2018ring",
      title: "Sivi qanday",
      titleGradient: "ishlashini ko\u2018ring",
      placeholder: "Video tez kunda",
    },
    about: {
      label: "Biz haqimizda",
      title: "Kelajak avlod",
      titleGradient: "iqtidorlari",
      titlePost: "uchun yaratilgan",
      p1: "Markaziy Osiyo va undan tashqaridagi millionlab iqtidorli odamlar eskirgan ish qidirish vositalari bilan qiynalmoqda. Rezyumelar imkoniyatlarni ko\u2018rsatmaydi. Ish o\u2018rinlari o\u2018nlab platformalar bo\u2018ylab tarqalgan. Intervyuga tayyorgarlik mavjud emas.",
      p2Highlight: "Sivi buni o\u2018zgartiradi.",
      p2: "Biz AI quvvatli rezyume intellekti, ko\u2018p manbali vakansiya yig\u2018ish va shaxsiylashtirilgan intervyu koachingini birlashtiramiz \u2014 barchasi oddiy Telegram chat orqali.",
      founderRole: "Asoschi va bosh direktor",
      founderBio: "IT da 5+ yillik tajriba \u2022 SWE @ Unicon",
    },
    cta: {
      titleLine1: "Karyerangiz darajasini",
      titleLine2: "oshirishga",
      titleGradient: "tayyormisiz?",
      subtitle:
        "Yaxshiroq rezyume yaratish, yaxshiroq ish topish va intervyularga tayyorgarlik ko\u2018rish uchun Sivi'dan foydalanadigan minglab ish izlovchilarga qo\u2018shiling.",
      button: "Telegramda boshlash",
    },
    footer: {
      tagline: "AI karyera agenti",
      features: "Imkoniyatlar",
      pricing: "Narxlar",
      about: "Biz haqimizda",
      telegram: "Telegram",
      rights: "Barcha huquqlar himoyalangan.",
    },
    faq: {
      title: "Ko'p so'raladigan savollar",
      items: [
        {
          q: "Toshkentda qanday ish topish mumkin?",
          a: "Eng tez yo'l — Sivi'dan foydalanish. Bu Telegramdagi AI karyera agenti bo'lib, O'zbekistondagi barcha yirik manbalardan vakansiyalarni bir lentaga to'playdi. hh.uz, OLX.uz, IshPlus, OsonIsh va o'nlab Telegram kanallarini alohida tekshirish o'rniga, hammasini bir chatda olasiz — har 2 soatda yangilanadi.",
        },
        {
          q: "O'zbekistonda onlayn ish qayerdan topsa bo'ladi?",
          a: "Sivi hh.uz, OLX.uz, IshPlus.uz, OsonIsh.uz, Ish.uz, Vacandi.uz, Ishkop.uz, davlat portali Argos.uz va 17+ professional Telegram kanallaridan 60 000+ aktiv vakansiyani to'playdi. O'zbek, rus yoki ingliz tilida qidiring — Sivi topadi.",
        },
        {
          q: "Sivi'da qanday ishlar topish mumkin?",
          a: "Har qanday. Sivi savdo, marketing, moliya, buxgalteriya, HR, ta'lim, sog'liqni saqlash, mehmonxona, logistika, qurilish, chakana savdo, mijozlarga xizmat, ma'muriyat, davlat lavozimlari va boshqalar bo'yicha vakansiyalarni to'playdi — boshlang'ich darajadan yuqori rahbariyatgacha.",
        },
        {
          q: "O'zbekistonda yarim stavkali yoki masofaviy ish bormi?",
          a: "Ha. Sivi yarim stavkali, to'liq stavkali, smenali va frilansi vakansiyalarni kuzatadi. Mahalliy va xalqaro ish beruvchilardan masofaviy va gibrid rollarni ham to'playdi — mijozlarga qo'llab-quvvatlash, marketing, dizayn, yozuv, buxgalteriya va IT.",
        },
        {
          q: "Tajribasiz ish topsa bo'ladimi?",
          a: "Albatta. Sivi to'playdigan vakansiyalarning katta qismi boshlang'ich daraja yoki \"tajriba talab etilmaydi\" — chakana savdo, call-markazlar, yetkazib berish, mehmonxona, savdo va ma'muriy ishlarda keng tarqalgan. AI boshlang'ichlar uchun filtrlashi va hech qachon ishlamagan bo'lsangiz ham rezyume tuzishga yordam beradi.",
        },
        {
          q: "Toshkentda yuqori maoshli ishlar bormi?",
          a: "Ha. Sivi bank, moliya, boshqaruv, savdo rahbariyati va ixtisoslashgan texnik lavozimlardagi yuqori maoshli rollarni ko'rsatadi. 10 ta platforma va Telegram kanallaridan ma'lumot to'plangani sababli, odatdagi doskalarga chiqmasdan to'ldirib ketadigan premium vakansiyalarni ham ko'rasiz.",
        },
        {
          q: "O'zbekistonda davlat ishlarini qanday topish mumkin?",
          a: "Sivi Argos.uz bilan bevosita integratsiyalashgan va barcha mintaqalar — Toshkent, Samarqand, Buxoro va boshqalar bo'yicha 3 000+ aktiv davlat vakansiyasini kuzatadi. Telegram orqali ko'ring, filtrlang va murojaat qiling.",
        },
        {
          q: "Sivi qaysi Telegram kanallarini kuzatadi?",
          a: "Sivi O'zbekistondagi 17+ yetakchi vakansiya kanallarini skanerlaydi: click_jobs, Tashkent_Jobs, doda_jobs, ishmi_ish, hrjobuz, edu_vakansiya, UstozShogird, linkedinjobsuzbekistan, uzbekistanishborwork, UzjobsUz, uzdev_jobs, python_djangojobs, data_ish, ExampleuzIT, itpark_uz, vacancyuzairports va boshqalar.",
        },
        {
          q: "O'zbekiston mehnat bozori uchun rezyume qanday yozish yoki yaxshilash mumkin?",
          a: "Sivi'ning AI rezyume yaratuvchisi jarayonni bosqichma-bosqich o'tkazadi — tajriba, ta'lim va ko'nikmalar haqida so'raydi, so'ngra ingliz, rus yoki o'zbek tilida professional rezyume yaratadi. Resume Intelligence mavjud rezyumengizni tekshirishi, kamchiliklarini ko'rsatishi va bo'limlarni maqsadli lavozimlarga mos qayta yozishi mumkin.",
        },
        {
          q: "Intervyuga qanday tayyorlanish mumkin?",
          a: "Sivi rezyumengiz va murojaat qiladigan lavozimga moslashtirilgan mock savollar yaratadi. Siz Telegram ichida mashq qilasiz, AI javoblaringizni baholaydi va fikr-mulohaza beradi — savdo, bank, ta'lim, IT va boshqa sohalarda ishlaydi.",
        },
        {
          q: "Sivi hh.uz yoki OLX'dan yaxshiroqmi?",
          a: "hh.uz va OLX — alohida vakansiya doskalar. Sivi ikkisini ham yana 8 ta platforma va 17+ Telegram kanaliga qo'shib to'playdi, shuning uchun bir joyda ancha keng bozorni ko'rasiz. Bundan tashqari, Sivi AI rezyume tekshiruvi va intervyuga tayyorgarlik taklif qiladi — oddiy vakansiya doskalari buni qilmaydi.",
        },
        {
          q: "Sivi bepulmi?",
          a: "Ha — 60 000+ vakansiyani ko'rib chiqish, AI rezyume yaratish va mock intervyular o'tkazish bepul.",
        },
        {
          q: "Ishlar qanchalik tez-tez yangilanadi?",
          a: "Har 2 soatda. Sivi muddati o'tgan e'lonlarni avtomatik o'chiradi, shuning uchun vaqtingizni behuda sarflamaysiz.",
        },
      ],
    },
  },

  ru: {
    nav: {
      features: "Возможности",
      howItWorks: "Как это работает",
      pricing: "Цены",
      about: "О нас",
      tryFree: "Попробовать",
    },
    hero: {
      titlePre: "Ваш",
      titleGradient: "AI карьерный",
      titlePost: "агент",
      subtitle:
        "Создавайте лучшие резюме. Находите лучшие вакансии. Проходите собеседования \u2014",
      subtitleHighlight: "всё в чате.",
      subtitleEnd: "Ваш AI карьерный помощник прямо в Telegram.",
      cta: "Начать в Telegram",
      learnMore: "Узнать больше",
      statFreeValue: "Бесплатно",
      statFreeLabel: "Для старта",
      statLangValue: "4",
      statLangLabel: "Языка",
      statAiValue: "AI",
      statAiLabel: "Технология",
    },
    features: {
      label: "Что мы делаем",
      title: "Всё, что нужно для",
      titleGradient: "вашей следующей работы",
      resumeTitle: "AI конструктор резюме",
      resumeDesc:
        "Загрузите резюме или ответьте на вопросы \u2014 AI создаст профессиональное резюме, подчёркивающее ваши сильные стороны.",
      jobTitle: "Умный подбор вакансий",
      jobDesc:
        "Мы собираем вакансии с сайтов, компаний и Telegram-каналов \u2014 и подбираем их под ваши навыки с помощью AI.",
      interviewTitle: "Подготовка к собеседованию",
      interviewDesc:
        "Практикуйтесь с AI-вопросами по вашей целевой должности. Получайте оценки, обратную связь и улучшайтесь.",
    },
    howItWorks: {
      label: "Простой процесс",
      title: "Как это",
      titleGradient: "работает",
      step1Title: "Запустите бота",
      step1Desc:
        "Откройте @SiviAIBot в Telegram и нажмите Start. Без регистрации.",
      step2Title: "Создайте резюме",
      step2Desc:
        "Загрузите существующее резюме или ответьте на вопросы. AI сделает остальное.",
      step3Title: "Получите подборку",
      step3Desc:
        "AI просматривает тысячи вакансий и находит подходящие для вашего профиля.",
      step4Title: "Пройдите собеседование",
      step4Desc:
        "Практикуйтесь с подобранными вопросами и получайте полезную обратную связь.",
    },
    video: {
      label: "Смотрите в действии",
      title: "Смотрите, как",
      titleGradient: "работает Sivi",
      placeholder: "Видео скоро",
    },
    about: {
      label: "О нас",
      title: "Создано для",
      titleGradient: "нового поколения",
      titlePost: "талантов",
      p1: "По всей Центральной Азии и за её пределами миллионы талантливых людей сталкиваются с устаревшими инструментами поиска работы. Резюме не раскрывают потенциал. Вакансии разбросаны по десяткам платформ. Подготовка к собеседованию отсутствует.",
      p2Highlight: "Sivi меняет это.",
      p2: "Мы объединяем AI-аналитику резюме, агрегацию вакансий из множества источников и персонализированную подготовку к собеседованиям \u2014 всё через простой чат в Telegram.",
      founderRole: "Основатель и CEO",
      founderBio: "5+ лет в IT \u2022 SWE @ Unicon",
    },
    cta: {
      titleLine1: "Готовы прокачать",
      titleLine2: "",
      titleGradient: "карьеру?",
      subtitle:
        "Присоединяйтесь к тысячам соискателей, использующих Sivi для создания лучших резюме, поиска лучших вакансий и подготовки к собеседованиям.",
      button: "Начните в Telegram",
    },
    footer: {
      tagline: "AI карьерный агент",
      features: "Возможности",
      pricing: "Цены",
      about: "О нас",
      telegram: "Telegram",
      rights: "Все права защищены.",
    },
    faq: {
      title: "Часто задаваемые вопросы",
      items: [
        {
          q: "Как найти работу в Ташкенте?",
          a: "Самый быстрый способ — Sivi, AI карьерный агент в Telegram, который агрегирует вакансии из всех крупных источников Узбекистана в одну ленту. Вместо того чтобы проверять hh.uz, OLX.uz, IshPlus, OsonIsh и десятки Telegram-каналов по отдельности, вы получаете всё в одном чате, обновляемом каждые 2 часа.",
        },
        {
          q: "Где найти работу в Узбекистане онлайн?",
          a: "Sivi агрегирует 60 000+ активных вакансий с hh.uz, OLX.uz, IshPlus.uz, OsonIsh.uz, Ish.uz, Vacandi.uz, Ishkop.uz, государственного портала Argos.uz и 17+ профессиональных Telegram-каналов. Ищите на русском, узбекском или английском — Sivi найдёт.",
        },
        {
          q: "Какие вакансии можно найти на Sivi?",
          a: "Любые. Sivi агрегирует вакансии в сфере продаж, маркетинга, финансов, бухгалтерии, HR, образования, здравоохранения, гостиничного бизнеса, логистики, строительства, торговли, клиентского сервиса, администрирования, государственных должностей и многого другого — от начального уровня до топ-менеджмента.",
        },
        {
          q: "Есть ли в Узбекистане вакансии с частичной занятостью или удалённой работой?",
          a: "Да. Sivi отслеживает вакансии с частичной, полной и сменной занятостью, а также фриланс. Агрегирует удалённые и гибридные роли от местных и международных работодателей — поддержка клиентов, маркетинг, дизайн, копирайтинг, бухгалтерия и IT.",
        },
        {
          q: "Можно ли найти работу без опыта?",
          a: "Конечно. Большая часть вакансий на Sivi — начального уровня или «без опыта»: розничная торговля, call-центры, доставка, гостиничный бизнес, продажи, административная работа. AI может отфильтровать вакансии для начинающих, а также помочь составить резюме, даже если вы никогда не работали.",
        },
        {
          q: "Есть ли высокооплачиваемые вакансии в Ташкенте?",
          a: "Да. Sivi показывает старшие и высокооплачиваемые должности в банковской сфере, финансах, менеджменте, руководстве продажами и специализированных технических позициях. Агрегируя данные с 10 платформ и Telegram-каналов, вы видите премиум-вакансии, которые часто заполняются до появления на обычных досках.",
        },
        {
          q: "Как найти государственные вакансии в Узбекистане?",
          a: "Sivi напрямую интегрирован с Argos.uz и отслеживает 3 000+ активных государственных вакансий по всем регионам — Ташкент, Самарканд, Бухара и другие. Просматривайте, фильтруйте и подавайте заявки прямо из Telegram.",
        },
        {
          q: "Какие Telegram-каналы с вакансиями отслеживает Sivi?",
          a: "Sivi сканирует 17+ ведущих каналов вакансий Узбекистана: click_jobs, Tashkent_Jobs, doda_jobs, ishmi_ish, hrjobuz, edu_vakansiya, UstozShogird, linkedinjobsuzbekistan, uzbekistanishborwork, UzjobsUz, uzdev_jobs, python_djangojobs, data_ish, ExampleuzIT, itpark_uz, vacancyuzairports и другие.",
        },
        {
          q: "Как написать или улучшить резюме для рынка труда Узбекистана?",
          a: "Конструктор резюме Sivi проведёт вас через весь процесс — спросит об опыте, образовании и навыках, затем создаст профессиональное резюме на английском, русском или узбекском. Resume Intelligence может также проверить ваше текущее резюме, указать на недостатки и переписать разделы под нужные вакансии.",
        },
        {
          q: "Как подготовиться к собеседованию?",
          a: "Sivi генерирует mock-вопросы, адаптированные под ваше резюме и конкретную вакансию. Вы практикуетесь в Telegram, AI оценивает ответы и даёт обратную связь — работает для любой отрасли: продажи, банки, образование, IT и другие.",
        },
        {
          q: "Sivi лучше, чем hh.uz или OLX?",
          a: "hh.uz и OLX — это отдельные доски вакансий. Sivi агрегирует обе плюс ещё 8 платформ и 17+ Telegram-каналов, так что вы видите гораздо более широкий рынок в одном месте. Кроме того, Sivi предлагает AI-проверку резюме и подготовку к собеседованиям, чего обычные доски не предоставляют.",
        },
        {
          q: "Sivi бесплатный?",
          a: "Да — просмотр 60 000+ вакансий, создание AI-резюме и mock-интервью бесплатны.",
        },
        {
          q: "Как часто обновляются вакансии?",
          a: "Каждые 2 часа. Sivi автоматически удаляет устаревшие объявления, чтобы вы не тратили время впустую.",
        },
      ],
    },
  },

  en: {
    nav: {
      features: "Features",
      howItWorks: "How It Works",
      pricing: "Pricing",
      about: "About",
      tryFree: "Try Free",
    },
    hero: {
      titlePre: "Your",
      titleGradient: "AI Career",
      titlePost: "Agent",
      subtitle: "Build better CVs. Find better jobs. Nail interviews \u2014",
      subtitleHighlight: "all in chat.",
      subtitleEnd: "Your AI-powered career assistant, right on Telegram.",
      cta: "Start on Telegram",
      learnMore: "Learn More",
      statFreeValue: "Free",
      statFreeLabel: "To start",
      statLangValue: "4",
      statLangLabel: "Languages",
      statAiValue: "AI",
      statAiLabel: "Powered",
    },
    features: {
      label: "What We Do",
      title: "Everything you need to",
      titleGradient: "land your next role",
      resumeTitle: "AI Resume Builder",
      resumeDesc:
        "Upload your CV or answer smart questions \u2014 our AI creates a polished, professional resume that highlights your strengths.",
      jobTitle: "Smart Job Matching",
      jobDesc:
        "We aggregate vacancies from job boards, company sites, and Telegram channels \u2014 then match them to your skills using AI.",
      interviewTitle: "Interview Prep",
      interviewDesc:
        "Practice with AI-generated questions tailored to your target role. Get scored, get feedback, get better.",
    },
    howItWorks: {
      label: "Simple Process",
      title: "How it",
      titleGradient: "works",
      step1Title: "Start the Bot",
      step1Desc:
        "Open @SiviAIBot on Telegram and hit Start. No sign-ups, no forms.",
      step2Title: "Build Your Resume",
      step2Desc:
        "Upload an existing CV or answer guided questions. Our AI does the rest.",
      step3Title: "Get Matched",
      step3Desc:
        "AI scans thousands of vacancies and finds the ones that fit your profile.",
      step4Title: "Ace Interviews",
      step4Desc:
        "Practice with tailored questions and get actionable feedback to improve.",
    },
    video: {
      label: "See It In Action",
      title: "Watch how",
      titleGradient: "Sivi works",
      placeholder: "Video Coming Soon",
    },
    about: {
      label: "About",
      title: "Built for the",
      titleGradient: "next generation",
      titlePost: "of talent",
      p1: "Across Central Asia and beyond, millions of talented people struggle with outdated job search tools. Resumes don\u2019t showcase potential. Jobs are scattered across dozens of platforms. Interview prep is nonexistent.",
      p2Highlight: "Sivi changes that.",
      p2: "We combine AI-powered resume intelligence, multi-source job aggregation, and personalized interview coaching \u2014 all accessible through a simple Telegram chat.",
      founderRole: "Founder & CEO",
      founderBio: "5+ years in IT \u2022 SWE @ Unicon",
    },
    cta: {
      titleLine1: "Ready to level up",
      titleLine2: "",
      titleGradient: "your career?",
      subtitle:
        "Join thousands of job seekers using Sivi to build better resumes, find better jobs, and prepare for interviews.",
      button: "Start on Telegram",
    },
    footer: {
      tagline: "AI Career Agent",
      features: "Features",
      pricing: "Pricing",
      about: "About",
      telegram: "Telegram",
      rights: "All rights reserved.",
    },
    faq: {
      title: "Frequently Asked Questions",
      items: [
        {
          q: "How do I find a job in Tashkent?",
          a: "The fastest way is to use Sivi — an AI career agent on Telegram that aggregates vacancies from every major source in Uzbekistan into one feed. Instead of checking hh.uz, OLX.uz, IshPlus, OsonIsh, and a dozen Telegram channels separately, you get all of them in one chat, updated every 2 hours.",
        },
        {
          q: "Where can I find jobs in Uzbekistan online?",
          a: "Sivi aggregates 60,000+ active vacancies from hh.uz, OLX.uz, IshPlus.uz, OsonIsh.uz, Ish.uz, Vacandi.uz, Ishkop.uz, the government portal Argos.uz, and 17+ professional Telegram channels. Whether you search in English, Russian, or Uzbek, Sivi finds it.",
        },
        {
          q: "What kind of jobs can I find on Sivi?",
          a: "Every kind. Sivi aggregates vacancies across sales, marketing, finance, accounting, HR, teaching, healthcare, hospitality, logistics, construction, retail, customer service, administration, government roles, and more — from entry-level to senior management.",
        },
        {
          q: "Are there part-time or remote jobs in Uzbekistan?",
          a: "Yes. Sivi tracks part-time, full-time, shift-based, and freelance vacancies. It also aggregates remote and hybrid roles from local and international employers, including customer support, marketing, design, writing, accounting, and tech positions.",
        },
        {
          q: "Can I find a job without experience?",
          a: "Absolutely. A large share of vacancies Sivi aggregates are entry-level or 'no experience required' — common in retail, call centers, delivery, hospitality, sales, and admin work. The AI can filter specifically for beginner-friendly jobs, and it can help you build a first CV even if you've never worked before.",
        },
        {
          q: "Are there high-paying jobs in Tashkent?",
          a: "Yes. Sivi surfaces senior and well-paid roles across banking, finance, management, sales leadership, and specialized technical positions. Because we aggregate from 10 platforms plus Telegram channels, you see premium listings that often get filled before hitting mainstream boards.",
        },
        {
          q: "How do I find government jobs in Uzbekistan?",
          a: "Sivi is directly integrated with Argos.uz and tracks 3,000+ active government vacancies covering all regions — Tashkent, Samarkand, Bukhara, and beyond. Browse, filter, and apply straight from Telegram.",
        },
        {
          q: "Which Telegram channels does Sivi track for jobs?",
          a: "Sivi scans 17+ of the top vacancy channels in Uzbekistan, including click_jobs, Tashkent_Jobs, doda_jobs, ishmi_ish, hrjobuz, edu_vakansiya, UstozShogird, linkedinjobsuzbekistan, uzbekistanishborwork, UzjobsUz, uzdev_jobs, python_djangojobs, data_ish, ExampleuzIT, itpark_uz, vacancyuzairports, and more.",
        },
        {
          q: "How do I write or improve my CV for the Uzbekistan job market?",
          a: "Sivi's AI resume builder walks you through it — it asks about your experience, education, and skills, then generates a professional CV in English, Russian, or Uzbek. Resume Intelligence can also review your existing CV, flag what's missing, and rewrite sections to match the roles you're targeting.",
        },
        {
          q: "How can I prepare for a job interview?",
          a: "Sivi generates mock interview questions tailored to your resume and the exact role you're applying for. You practice inside Telegram and the AI scores your answers and gives feedback — works for any industry: sales, banking, teaching, tech, and more.",
        },
        {
          q: "Is Sivi better than hh.uz or OLX?",
          a: "hh.uz and OLX are single job boards — Sivi aggregates both of them plus 8 more platforms and 17+ Telegram channels, so you see a much wider slice of the market in one place. On top of that, Sivi adds AI resume review and interview prep, which regular job boards don't offer.",
        },
        {
          q: "Is Sivi free?",
          a: "Yes — you can browse all 60,000+ vacancies, build your AI resume, and run mock interviews for free.",
        },
        {
          q: "How often are jobs updated?",
          a: "Every 2 hours. Sivi auto-removes expired listings so you never waste time on dead vacancies.",
        },
      ],
    },
  },
} as const;

type DeepString<T> = T extends string
  ? string
  : T extends readonly (infer U)[]
  ? readonly DeepString<U>[]
  : { [K in keyof T]: DeepString<T[K]> };

export type Translations = DeepString<(typeof translations)["uz"]>;
export default translations;
