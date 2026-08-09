from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
from pathlib import Path
from html import escape
from http.cookies import SimpleCookie
import sqlite3, os, secrets, hmac, hashlib, csv, io, mimetypes
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / 'static'
DATA_DIR = BASE_DIR / 'data'
DB_PATH = DATA_DIR / 'academy.db'
HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', '8000'))
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'viral2026')
SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-secret-in-production')

SESSIONS = {}

NAV = {
    'fr': [
        ('/', 'Accueil'),
        ('/formation', 'Formation'),
        ('/programme', 'Programme'),
        ('/projets', 'Projets'),
        ('/a-propos', 'À propos'),
        ('/contact', 'Contact'),
    ],
    'ar': [
        ('/', 'الرئيسية'),
        ('/formation', 'التكوين'),
        ('/programme', 'البرنامج'),
        ('/projets', 'المشاريع'),
        ('/a-propos', 'من نحن'),
        ('/contact', 'تواصل معنا'),
    ],
}

PROGRAM = {
    'fr': [
        ('01', 'Fondations IA & Prompting', 'Comprendre l’IA générative, écrire de bons prompts et définir ton projet de marque.', ['IA générative', 'Prompt Engineering', 'Identité de projet', 'Premiers contenus']),
        ('02', 'Création d’images & Design', 'Créer des visuels cohérents et professionnels pour les réseaux sociaux et la publicité.', ['Images IA', 'Posts & stories', 'Visuels produit', 'Mini campagne']),
        ('03', 'Reels, Vidéo & Montage', 'Passer d’une idée à une vidéo courte prête à publier.', ['Scripts', 'Reels', 'Sous-titres', 'Montage assisté par IA']),
        ('04', 'Marketing & Publicité', 'Construire des contenus qui captent l’attention et présentent une offre clairement.', ['Copywriting', 'Publicités', 'Calendrier contenu', 'Campagne social media']),
        ('05', 'Site Web & Workflow', 'Créer le site de ton projet et structurer un workflow client simple.', ['Site web avec IA', 'Pages essentielles', 'Formulaires', 'Livraison client']),
        ('06', 'Portfolio & Projet Final', 'Finaliser une présence digitale complète et préparer sa présentation.', ['Portfolio', 'Instagram', 'Site final', 'Présentation de projet']),
    ],
    'ar': [
        ('01', 'أساسيات الذكاء الاصطناعي وكتابة الأوامر', 'فهم الذكاء الاصطناعي التوليدي، كتابة أوامر فعالة، وتحديد فكرة مشروعك وهويته.', ['الذكاء الاصطناعي التوليدي', 'كتابة الأوامر', 'هوية المشروع', 'أول محتوى']),
        ('02', 'إنشاء الصور والتصميم', 'إنشاء صور ومرئيات متناسقة واحترافية للسوشيال ميديا والإعلانات.', ['صور بالذكاء الاصطناعي', 'منشورات وستوري', 'صور المنتجات', 'حملة مصغرة']),
        ('03', 'الريلز والفيديو والمونتاج', 'تحويل الفكرة إلى فيديو قصير جاهز للنشر.', ['السيناريو', 'Reels', 'الترجمة التلقائية', 'مونتاج بمساعدة الذكاء الاصطناعي']),
        ('04', 'التسويق والإعلانات', 'إنشاء محتوى يجذب الانتباه ويعرض الخدمة أو المنتج بوضوح.', ['كتابة إعلانية', 'إعلانات', 'خطة محتوى', 'حملة سوشيال ميديا']),
        ('05', 'الموقع الإلكتروني وسير العمل', 'إنشاء موقع لمشروعك وتنظيم طريقة بسيطة للتعامل مع العميل.', ['موقع بالذكاء الاصطناعي', 'الصفحات الأساسية', 'النماذج', 'تسليم العمل للعميل']),
        ('06', 'الـPortfolio والمشروع النهائي', 'إكمال حضور رقمي متكامل والاستعداد لعرض المشروع.', ['Portfolio', 'Instagram', 'الموقع النهائي', 'عرض المشروع']),
    ],
}

PROJECTS = {
    'fr': [
        ('Brand IA', 'Construis une identité visuelle cohérente : logo, ton, couleurs et contenus.'),
        ('Instagram Pro', 'Crée une page dédiée au projet et alimente-la avec posts, stories et Reels.'),
        ('Campagne Publicitaire', 'Prépare une campagne complète : concept, visuels, texte publicitaire et vidéo courte.'),
        ('Site Web', 'Conçois un site responsive avec pages, présentation de l’offre et formulaire de contact.'),
    ],
    'ar': [
        ('هوية رقمية بالذكاء الاصطناعي', 'ابنِ هوية متناسقة: شعار، أسلوب، ألوان ومحتوى.'),
        ('Instagram احترافي', 'أنشئ صفحة خاصة بالمشروع وانشر فيها منشورات وستوري وReels.'),
        ('حملة إعلانية', 'جهز حملة كاملة: الفكرة، الصور، النص الإعلاني والفيديو القصير.'),
        ('موقع إلكتروني', 'صمّم موقعا متجاوبا يعرض المشروع والخدمات ويضم نموذج تواصل.'),
    ],
}


def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DATA_DIR.mkdir(exist_ok=True)
    with db_connect() as conn:
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            city TEXT,
            objective TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        ''')


def sign(value):
    return hmac.new(SECRET_KEY.encode(), value.encode(), hashlib.sha256).hexdigest()


def make_session():
    token = secrets.token_urlsafe(24)
    SESSIONS[token] = {'admin': True, 'created_at': datetime.utcnow().isoformat()}
    return f'{token}.{sign(token)}'


def valid_session(raw):
    if not raw or '.' not in raw:
        return False
    token, sig = raw.rsplit('.', 1)
    return hmac.compare_digest(sig, sign(token)) and token in SESSIONS


def get_lang(handler, parsed=None):
    if parsed is None:
        parsed = urlparse(handler.path)
    query = parse_qs(parsed.query)
    requested = query.get('lang', [''])[0]
    if requested in ('fr', 'ar'):
        return requested
    cookie = SimpleCookie(handler.headers.get('Cookie', ''))
    if 'vd_lang' in cookie and cookie['vd_lang'].value in ('fr', 'ar'):
        return cookie['vd_lang'].value
    return 'fr'


def base_page(title, content, path='/', lang='fr', description=None):
    rtl = lang == 'ar'
    desc = description or (
        'تكوين عملي في الذكاء الاصطناعي وإنشاء المحتوى والريلز والإعلانات والمواقع الإلكترونية.'
        if rtl else
        'Formation pratique en intelligence artificielle, création de contenu, Reels, publicité et sites web.'
    )
    nav = ''.join(
        f'<a class="nav-link {"active" if href == path else ""}" href="{href}">{label}</a>'
        for href, label in NAV[lang]
    )
    current = quote(path if path.startswith('/') else '/', safe='/')
    signup = 'التسجيل' if rtl else 'S’inscrire'
    menu_label = 'فتح القائمة' if rtl else 'Ouvrir le menu'
    footer_nav = 'التنقل' if rtl else 'Navigation'
    footer_contact = 'تواصل' if rtl else 'Contact'
    footer_text = 'تعلّم. طبّق. وابنِ مشروعاً حقيقياً بالذكاء الاصطناعي.' if rtl else 'Apprends. Applique. Crée un projet concret avec l’IA.'
    write_us = 'راسلنا' if rtl else 'Nous écrire'
    prereg = 'التسجيل الأولي' if rtl else 'Pré-inscription'
    copyright_text = 'تكوين عملي في الذكاء الاصطناعي' if rtl else 'Formation pratique en IA'
    html_class = 'rtl' if rtl else 'ltr'
    return f'''<!doctype html>
<html lang="{lang}" dir="{'rtl' if rtl else 'ltr'}" class="{html_class}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} | Viral Digitale Academy</title>
  <meta name="description" content="{escape(desc)}">
  <meta name="theme-color" content="#07101f">
  <link rel="icon" href="/static/img/logo.png">
  <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
  <div class="ambient ambient-one"></div><div class="ambient ambient-two"></div>
  <header class="site-header">
    <a class="brand" href="/"><img src="/static/img/logo.png" alt="Viral Digitale Academy"><span><b>VIRAL DIGITALE</b><small>ACADEMY</small></span></a>
    <button class="menu-btn" aria-label="{menu_label}" aria-expanded="false">☰</button>
    <nav class="nav">{nav}
      <div class="lang-switch" aria-label="Language"><a class="{'active' if lang=='fr' else ''}" href="/set-lang?lang=fr&next={current}">FR</a><span>/</span><a class="{'active' if lang=='ar' else ''}" href="/set-lang?lang=ar&next={current}">العربية</a></div>
      <a class="btn btn-sm" href="/inscription">{signup}</a>
    </nav>
  </header>
  <main>{content}</main>
  <footer class="footer">
    <div class="footer-grid">
      <div><div class="brand footer-brand"><img src="/static/img/logo.png" alt=""><span><b>VIRAL DIGITALE</b><small>ACADEMY</small></span></div><p>{footer_text}</p></div>
      <div><h4>{footer_nav}</h4><a href="/formation">{NAV[lang][1][1]}</a><a href="/programme">{NAV[lang][2][1]}</a><a href="/projets">{NAV[lang][3][1]}</a></div>
      <div><h4>{footer_contact}</h4><a href="/contact">{write_us}</a><a href="/inscription">{prereg}</a><a href="https://instagram.com/viral_digitale" target="_blank" rel="noopener">@viral_digitale</a></div>
    </div>
    <div class="copyright">© {datetime.now().year} Viral Digitale Academy — {copyright_text}.</div>
  </footer>
  <script src="/static/js/main.js"></script>
</body>
</html>'''.encode('utf-8')


def home_page(lang):
    if lang == 'ar':
        cards = ''.join(f'<article class="mini-card"><span>{n}</span><h3>{t}</h3><p>{d}</p></article>' for n,t,d,_ in PROGRAM['ar'][:3])
        content = f'''
<section class="hero container">
  <div class="hero-copy reveal">
    <div class="eyebrow">تكوين عملي • 6 أشهر • للمبتدئين</div>
    <h1>أتقن الذكاء الاصطناعي.<br><span>وابنِ مستقبلك.</span></h1>
    <p class="lead">تكوين تطبيقي قائم على مشروع حقيقي: تتعلم إنشاء الصور والريلز والإعلانات والموقع الإلكتروني، ثم تجمع أعمالك في Portfolio احترافي.</p>
    <div class="hero-actions"><a class="btn" href="/inscription">أريد التسجيل</a><a class="btn btn-ghost" href="/programme">شاهد البرنامج</a></div>
    <div class="stats"><div><b>6</b><span>أشهر</span></div><div><b>72h</b><span>ساعة تكوين</span></div><div><b>3h</b><span>في الأسبوع</span></div></div>
  </div>
  <div class="hero-visual reveal"><img src="/static/img/post-avenir.png" alt="أتقن الذكاء الاصطناعي"><div class="floating-note">1h30 شرح + 1h30 تطبيق</div></div>
</section>
<section class="section container center reveal"><div class="eyebrow">التعلم بالممارسة</div><h2>ليس مجرد أدوات.<br><span>بل مشروع رقمي متكامل.</span></h2><p class="section-intro">كل متدرب يختار مشروعاً منذ البداية ويطوره طوال التكوين: الهوية، Instagram، المحتوى، الإعلانات والموقع الإلكتروني.</p></section>
<section class="container cards-3">{cards}</section>
<section class="section split container reveal"><div><div class="eyebrow">هدف واضح</div><h2>في النهاية سيكون لديك شيء حقيقي تعرضه.</h2><p>النتيجة المتوقعة هي Portfolio حي: صفحة Instagram متناسقة، صور، Reels، حملة إعلانية وموقع إلكتروني.</p><a class="text-link" href="/projets">اكتشف المشاريع ←</a></div><img class="feature-img" src="/static/img/post-contenu.png" alt="إنشاء المحتوى"></section>
<section class="cta container reveal"><div><div class="eyebrow">جاهز للبدء؟</div><h2>ابدأ من الصفر وتقدم خطوة بخطوة.</h2><p>لا تحتاج إلى اشتراك مدفوع لإتمام التمارين الأساسية.</p></div><a class="btn" href="/inscription">التسجيل الأولي</a></section>
'''
        return base_page('الرئيسية', content, '/', lang)
    cards = ''.join(f'<article class="mini-card"><span>{n}</span><h3>{t}</h3><p>{d}</p></article>' for n,t,d,_ in PROGRAM['fr'][:3])
    content = f'''
<section class="hero container">
  <div class="hero-copy reveal">
    <div class="eyebrow">FORMATION PRATIQUE • 6 MOIS • DÉBUTANTS</div>
    <h1>Maîtrise l’IA.<br><span>Crée ton avenir.</span></h1>
    <p class="lead">Une formation orientée projet pour apprendre à créer des images, Reels, publicités et un site web — puis construire un portfolio concret.</p>
    <div class="hero-actions"><a class="btn" href="/inscription">Je veux m’inscrire</a><a class="btn btn-ghost" href="/programme">Voir le programme</a></div>
    <div class="stats"><div><b>6</b><span>mois</span></div><div><b>72h</b><span>de formation</span></div><div><b>3h</b><span>par semaine</span></div></div>
  </div>
  <div class="hero-visual reveal"><img src="/static/img/post-avenir.png" alt="Maîtrise l'IA, crée ton avenir"><div class="floating-note">1h30 cours + 1h30 pratique</div></div>
</section>
<section class="section container center reveal"><div class="eyebrow">APPRENDRE EN FAISANT</div><h2>Pas seulement des outils.<br><span>Un projet digital complet.</span></h2><p class="section-intro">Chaque apprenant choisit un projet dès le début et l’améliore pendant toute la formation : identité, Instagram, contenu, publicité et site web.</p></section>
<section class="container cards-3">{cards}</section>
<section class="section split container reveal"><div><div class="eyebrow">OBJECTIF CONCRET</div><h2>À la fin, tu as quelque chose à montrer.</h2><p>Le résultat attendu est un portfolio vivant : une page Instagram cohérente, des visuels, des Reels, une campagne publicitaire et un site web.</p><a class="text-link" href="/projets">Découvrir les projets →</a></div><img class="feature-img" src="/static/img/post-contenu.png" alt="Création de contenu"></section>
<section class="cta container reveal"><div><div class="eyebrow">PRÊT(E) À COMMENCER ?</div><h2>Commence de zéro. Construis étape par étape.</h2><p>Aucun abonnement premium n’est obligatoire pour suivre les exercices essentiels.</p></div><a class="btn" href="/inscription">Pré-inscription</a></section>
'''
    return base_page('Accueil', content, '/', lang)


def formation_page(lang):
    if lang == 'ar':
        content = '''
<section class="page-hero container reveal"><div class="eyebrow">تكوين الذكاء الاصطناعي الإبداعي</div><h1>تكوين هدفه <span>الإنتاج والتطبيق</span> وليس الاستماع فقط.</h1><p>3 ساعات أسبوعياً: ساعة ونصف شرح وساعة ونصف تطبيق موجه.</p></section>
<section class="section container grid-2 reveal">
  <div class="panel"><h2>لمن هذا التكوين؟</h2><ul class="check-list"><li>المبتدئون المهتمون بالذكاء الاصطناعي</li><li>الطلبة والخريجون الجدد</li><li>صناع المحتوى</li><li>من يريد بدء خدمات Freelance</li><li>أصحاب المشاريع الصغيرة</li></ul></div>
  <div class="panel"><h2>ماذا ستتعلم؟</h2><ul class="check-list"><li>إنشاء صور ومرئيات بالذكاء الاصطناعي</li><li>تحضير سيناريوهات وReels</li><li>إنشاء إعلانات رقمية</li><li>بناء صفحة Instagram احترافية</li><li>إنشاء موقع إلكتروني للمشروع</li></ul></div>
</section>
<section class="section container reveal"><div class="eyebrow">المنهجية</div><h2>كل أسبوع = فهم + تطبيق</h2><div class="timeline"><div><b>1h30</b><h3>شرح</h3><p>مفاهيم بسيطة، أمثلة مباشرة وطريقة عمل واضحة.</p></div><div><b>1h30</b><h3>ورشة تطبيقية</h3><p>تطبيق مباشر على مشروع المتدرب.</p></div><div><b>كل شهر</b><h3>نتيجة ملموسة</h3><p>عمل جديد يضاف إلى الـPortfolio.</p></div></div></section>
<section class="section split container reveal"><img class="feature-img" src="/static/img/post-reussis.png" alt="تعلم وطبق"><div><div class="eyebrow">متاح للجميع</div><h2>أدوات مجانية أو لها نسخة مجانية.</h2><p>التمارين الأساسية مصممة لتكون قابلة للتنفيذ بدون ChatGPT Plus. يمكن عرض بعض الأدوات المدفوعة كتجربة، لكنها ليست شرطاً لإكمال المسار.</p><a class="btn" href="/programme">شاهد برنامج 6 أشهر</a></div></section>
'''
        return base_page('التكوين', content, '/formation', lang)
    content = '''
<section class="page-hero container reveal"><div class="eyebrow">FORMATION IA CRÉATIVE</div><h1>Une formation pensée pour <span>produire</span>, pas seulement écouter.</h1><p>3 heures par semaine : 1h30 d’explication et 1h30 de pratique guidée.</p></section>
<section class="section container grid-2 reveal">
  <div class="panel"><h2>Pour qui ?</h2><ul class="check-list"><li>Débutants curieux de l’IA</li><li>Étudiants et jeunes diplômés</li><li>Créateurs de contenu</li><li>Personnes qui veulent lancer un service freelance</li><li>Petits porteurs de projet</li></ul></div>
  <div class="panel"><h2>Ce que tu vas savoir faire</h2><ul class="check-list"><li>Créer des visuels avec l’IA</li><li>Préparer des scripts et Reels</li><li>Concevoir des publicités digitales</li><li>Structurer une page Instagram professionnelle</li><li>Créer un site web pour ton projet</li></ul></div>
</section>
<section class="section container reveal"><div class="eyebrow">MÉTHODE</div><h2>Une semaine = comprendre + appliquer</h2><div class="timeline"><div><b>1h30</b><h3>Explication</h3><p>Concepts simples, démonstrations et méthode.</p></div><div><b>1h30</b><h3>Exercice / atelier</h3><p>Application directe sur le projet personnel.</p></div><div><b>Chaque mois</b><h3>Livrable</h3><p>Un résultat concret à ajouter au portfolio.</p></div></div></section>
<section class="section split container reveal"><img class="feature-img" src="/static/img/post-reussis.png" alt="Apprends, applique, réussis"><div><div class="eyebrow">ACCESSIBLE</div><h2>Des outils gratuits ou avec version gratuite.</h2><p>La formation est conçue pour que les exercices de base restent accessibles sans ChatGPT Plus. Les outils premium peuvent être montrés en démonstration, mais ne sont pas indispensables au parcours principal.</p><a class="btn" href="/programme">Voir les 6 mois</a></div></section>
'''
    return base_page('Formation', content, '/formation', lang)


def programme_page(lang):
    cards = ''
    for n, title, desc, items in PROGRAM[lang]:
        tags = ''.join(f'<li>{escape(x)}</li>' for x in items)
        cards += f'<article class="program-card reveal"><div class="program-num">MOIS {n if lang=="fr" else n}</div><h2>{escape(title)}</h2><p>{escape(desc)}</p><ul>{tags}</ul></article>'
    if lang == 'ar':
        content = f'''
<section class="page-hero container reveal"><div class="eyebrow">72 ساعة • 6 أشهر</div><h1>برنامج يتقدم <span>مرحلة بمرحلة.</span></h1><p>كل شهر يضيف مهارة ونتيجة جديدة إلى نفس المشروع الشخصي حتى يصبح Portfolio متكاملاً.</p></section>
<section class="container program-grid">{cards}</section>
<section class="cta container reveal"><div><div class="eyebrow">النتيجة النهائية</div><h2>مشروع رقمي متكامل قابل للعرض.</h2><p>هوية + Instagram + صور + Reels + إعلانات + موقع إلكتروني.</p></div><a class="btn" href="/inscription">سجل اهتمامك</a></section>
'''
        return base_page('البرنامج', content, '/programme', lang)
    content = f'''
<section class="page-hero container reveal"><div class="eyebrow">72 HEURES • 6 MOIS</div><h1>Un programme qui avance <span>étape par étape.</span></h1><p>Chaque mois ajoute une nouvelle compétence et un nouveau livrable au même projet personnel.</p></section>
<section class="container program-grid">{cards}</section>
<section class="cta container reveal"><div><div class="eyebrow">RÉSULTAT FINAL</div><h2>Un projet digital complet à présenter.</h2><p>Identité + Instagram + Images + Reels + Publicités + Site Web.</p></div><a class="btn" href="/inscription">Je suis intéressé(e)</a></section>
'''
    return base_page('Programme', content, '/programme', lang)


def projets_page(lang):
    cards = ''.join(f'<article class="project-card reveal"><span>0{i+1}</span><h2>{escape(t)}</h2><p>{escape(d)}</p></article>' for i,(t,d) in enumerate(PROJECTS[lang]))
    if lang == 'ar':
        content = f'''
<section class="page-hero container reveal"><div class="eyebrow">التطبيق الحقيقي</div><h1>كل ما تتعلمه يتحول إلى <span>عمل داخل مشروعك.</span></h1><p>الهدف هو أن تنهي التكوين ومعك أعمال حقيقية تستطيع عرضها على عميل أو في ملفك المهني.</p></section>
<section class="container projects-grid">{cards}</section>
<section class="section container gallery reveal"><img src="/static/img/post-avenir.png" alt="مشروع ذكاء اصطناعي"><img src="/static/img/post-contenu.png" alt="محتوى رقمي"><img src="/static/img/post-reussis.png" alt="نتيجة التكوين"></section>
<section class="section container reveal"><div class="panel center"><div class="eyebrow">المشروع النهائي</div><h2>Brand + Instagram + Publicités + Reels + Site Web</h2><p class="section-intro">في النهاية يقدم المتدرب منظومة رقمية متكاملة ويشرح طريقة استعماله للذكاء الاصطناعي من الفكرة إلى النتيجة.</p></div></section>
'''
        return base_page('المشاريع', content, '/projets', lang)
    content = f'''
<section class="page-hero container reveal"><div class="eyebrow">PRATIQUE RÉELLE</div><h1>Chaque apprentissage devient <span>un livrable.</span></h1><p>L’objectif est de terminer la formation avec des travaux concrets à présenter à un client ou dans ton portfolio.</p></section>
<section class="container projects-grid">{cards}</section>
<section class="section container gallery reveal"><img src="/static/img/post-avenir.png" alt="Projet IA"><img src="/static/img/post-contenu.png" alt="Contenu digital"><img src="/static/img/post-reussis.png" alt="Résultat formation"></section>
<section class="section container reveal"><div class="panel center"><div class="eyebrow">PROJET FINAL</div><h2>Brand + Instagram + Publicités + Reels + Site Web</h2><p class="section-intro">À la fin, l’apprenant présente un écosystème digital complet et explique son workflow de création avec l’IA.</p></div></section>
'''
    return base_page('Projets', content, '/projets', lang)


def about_page(lang):
    if lang == 'ar':
        content='''
<section class="page-hero container reveal"><div class="eyebrow">VIRAL DIGITALE ACADEMY</div><h1>مهارات <span>مفيدة ويمكن رؤيتها.</span></h1><p>منهجنا يركز على التطبيق والإبداع والقدرة على تقديم نتيجة احترافية.</p></section>
<section class="section container grid-2 reveal"><div><h2>رؤيتنا</h2><p>جعل الذكاء الاصطناعي الإبداعي متاحاً للمبتدئين وتعليمهم كيف يستعملونه داخل سير عمل رقمي حقيقي.</p><p>لا ندّعي تحويل المبتدئ إلى مهندس ذكاء اصطناعي في بضعة أسابيع. الهدف هو تعليمه الاستعمال الذكي للأدوات المتاحة لإنتاج أعمال حقيقية.</p></div><div class="panel"><h3>مبادئنا</h3><ul class="check-list"><li>التطبيق قبل التكديس النظري</li><li>نتائج واضحة كل شهر</li><li>أدوات متاحة</li><li>مشروع شخصي مستمر</li><li>التحقق، الأخلاقيات وحماية البيانات</li></ul></div></section>
<section class="section split container reveal"><div><div class="eyebrow">الهوية</div><h2>ذكاء + إبداع + تكنولوجيا.</h2><p>شعار Viral Digitale Academy يجمع بين الدماغ والنور والدوائر الإلكترونية: تعلم، ابتكر، اربط الأفكار وحولها إلى نتائج.</p></div><img class="logo-showcase" src="/static/img/logo.png" alt="Viral Digitale Academy"></section>
'''
        return base_page('من نحن', content, '/a-propos', lang)
    content='''
<section class="page-hero container reveal"><div class="eyebrow">VIRAL DIGITALE ACADEMY</div><h1>Créer des compétences <span>visibles et utiles.</span></h1><p>Notre approche met l’accent sur la pratique, la création et la capacité à présenter un résultat professionnel.</p></section>
<section class="section container grid-2 reveal"><div><h2>Notre vision</h2><p>Rendre l’intelligence artificielle créative accessible aux débutants et leur apprendre à l’utiliser dans un vrai workflow de production digitale.</p><p>On ne cherche pas à transformer un débutant en ingénieur IA en quelques semaines. On lui apprend plutôt à utiliser intelligemment les outils disponibles pour produire des livrables concrets.</p></div><div class="panel"><h3>Nos principes</h3><ul class="check-list"><li>Pratique avant surcharge théorique</li><li>Résultats visibles chaque mois</li><li>Outils accessibles</li><li>Projet personnel continu</li><li>Éthique, vérification et respect des données</li></ul></div></section>
<section class="section split container reveal"><div><div class="eyebrow">IDENTITÉ</div><h2>Intelligence + créativité + technologie.</h2><p>Le symbole de Viral Digitale Academy combine le cerveau, la lumière et les circuits : apprendre, créer, connecter les idées et les transformer en résultats.</p></div><img class="logo-showcase" src="/static/img/logo.png" alt="Logo Viral Digitale Academy"></section>
'''
    return base_page('À propos', content, '/a-propos', lang)


def contact_page(lang):
    if lang == 'ar':
        content='''
<section class="page-hero container reveal"><div class="eyebrow">تواصل معنا</div><h1>لديك سؤال قبل <span>البدء؟</span></h1><p>أرسل لنا رسالتك وسنجيبك بالمعلومات المتعلقة بالتكوين.</p></section>
<section class="section container form-layout reveal"><div class="panel"><h2>Viral Digitale Academy</h2><p>تكوين عملي في الذكاء الاصطناعي التوليدي وصناعة المحتوى والحضور الرقمي.</p><div class="contact-lines"><span>Instagram</span><b>@viral_digitale</b><span>المستوى</span><b>مبتدئون</b><span>المدة</span><b>6 أشهر</b></div></div><form class="form-card" method="post" action="/contact"><label>الاسم الكامل<input name="full_name" required maxlength="100"></label><label>البريد الإلكتروني<input type="email" name="email" required maxlength="120"></label><label>الموضوع<input name="subject" maxlength="140"></label><label>الرسالة<textarea name="message" required maxlength="1500" rows="6"></textarea></label><button class="btn" type="submit">إرسال الرسالة</button></form></section>
'''
        return base_page('تواصل معنا', content, '/contact', lang)
    content='''
<section class="page-hero container reveal"><div class="eyebrow">CONTACT</div><h1>Une question avant de <span>commencer ?</span></h1><p>Écris-nous via le formulaire. Nous te répondrons avec les informations utiles sur la formation.</p></section>
<section class="section container form-layout reveal"><div class="panel"><h2>Viral Digitale Academy</h2><p>Formation pratique en IA générative, création de contenu et présence digitale.</p><div class="contact-lines"><span>Instagram</span><b>@viral_digitale</b><span>Public</span><b>Débutants</b><span>Durée</span><b>6 mois</b></div></div><form class="form-card" method="post" action="/contact"><label>Nom complet<input name="full_name" required maxlength="100"></label><label>Email<input type="email" name="email" required maxlength="120"></label><label>Sujet<input name="subject" maxlength="140"></label><label>Message<textarea name="message" required maxlength="1500" rows="6"></textarea></label><button class="btn" type="submit">Envoyer le message</button></form></section>
'''
    return base_page('Contact', content, '/contact', lang)


def registration_page(lang):
    if lang == 'ar':
        content='''
<section class="page-hero container reveal"><div class="eyebrow">التسجيل الأولي</div><h1>ابدأ مسارك في <span>الذكاء الاصطناعي الإبداعي.</span></h1><p>املأ النموذج لتسجيل اهتمامك. لا يتم طلب أي أداء مالي من خلال هذا الموقع.</p></section>
<section class="section container form-layout reveal"><div class="panel"><h2>ملخص التكوين</h2><div class="price-block"><span>المدة</span><b>6 أشهر</b><span>الإيقاع</span><b>3 ساعات / أسبوع</b><span>الصيغة</span><b>1h30 شرح + 1h30 تطبيق</b><span>المستوى</span><b>مبتدئ</b></div><p class="fine-print">التسجيل الأولي يعني أنك ترغب في أن يتم التواصل معك. الشروط التجارية النهائية يقدمها المركز بشكل منفصل.</p></div><form class="form-card" method="post" action="/inscription"><label>الاسم الكامل<input name="full_name" required maxlength="100"></label><label>البريد الإلكتروني<input type="email" name="email" required maxlength="120"></label><label>رقم الهاتف<input name="phone" required maxlength="30"></label><label>المدينة<input name="city" maxlength="80"></label><label>هدفك<select name="objective"><option>إنشاء محتوى بالذكاء الاصطناعي</option><option>Freelance / خدمات رقمية</option><option>مشروع شخصي</option><option>اكتشاف الذكاء الاصطناعي</option><option>هدف آخر</option></select></label><label class="consent"><input type="checkbox" required> أوافق على التواصل معي بخصوص التكوين.</label><button class="btn" type="submit">إرسال التسجيل الأولي</button></form></section>
'''
        return base_page('التسجيل', content, '/inscription', lang)
    content='''
<section class="page-hero container reveal"><div class="eyebrow">PRÉ-INSCRIPTION</div><h1>Commence ton parcours <span>IA créative.</span></h1><p>Remplis ce formulaire pour enregistrer ton intérêt. Aucun paiement n’est demandé sur ce site.</p></section>
<section class="section container form-layout reveal"><div class="panel"><h2>Récapitulatif</h2><div class="price-block"><span>Durée</span><b>6 mois</b><span>Rythme</span><b>3h / semaine</b><span>Format</span><b>1h30 cours + 1h30 pratique</b><span>Niveau</span><b>Débutant</b></div><p class="fine-print">La pré-inscription permet d’être recontacté. Les conditions commerciales définitives sont communiquées séparément par le centre.</p></div><form class="form-card" method="post" action="/inscription"><label>Nom complet<input name="full_name" required maxlength="100"></label><label>Email<input type="email" name="email" required maxlength="120"></label><label>Téléphone<input name="phone" required maxlength="30"></label><label>Ville<input name="city" maxlength="80"></label><label>Ton objectif<select name="objective"><option>Créer du contenu avec l’IA</option><option>Freelance / services digitaux</option><option>Projet personnel</option><option>Découvrir l’IA</option><option>Autre</option></select></label><label class="consent"><input type="checkbox" required> J’accepte d’être recontacté(e) au sujet de la formation.</label><button class="btn" type="submit">Envoyer ma pré-inscription</button></form></section>
'''
    return base_page('Inscription', content, '/inscription', lang)


def thank_you(lang, kind='inscription'):
    if lang == 'ar':
        if kind == 'contact':
            title='تم إرسال الرسالة'; text='شكراً لك. تم تسجيل رسالتك بنجاح.'
        else:
            title='تم استلام التسجيل الأولي'; text='شكراً لك. تم تسجيل معلوماتك وسيتم التواصل معك لاحقاً.'
        content=f'''<section class="success container"><div class="success-icon">✓</div><h1>{title}</h1><p>{text}</p><a class="btn" href="/">العودة إلى الرئيسية</a></section>'''
        return base_page(title, content, '/merci', lang)
    if kind == 'contact':
        title='Message envoyé'; text='Merci. Ton message a bien été enregistré.'
    else:
        title='Pré-inscription reçue'; text='Merci. Tes informations ont bien été enregistrées pour être recontacté(e).'
    content=f'''<section class="success container"><div class="success-icon">✓</div><h1>{title}</h1><p>{text}</p><a class="btn" href="/">Retour à l’accueil</a></section>'''
    return base_page(title, content, '/merci', lang)


def error_page(lang, message, back):
    if lang == 'ar':
        return base_page('خطأ', f'<section class="success container"><h1>النموذج غير مكتمل</h1><p>{escape(message)}</p><a class="btn" href="{back}">رجوع</a></section>', back, lang)
    return base_page('Erreur', f'<section class="success container"><h1>Formulaire incomplet</h1><p>{escape(message)}</p><a class="btn" href="{back}">Retour</a></section>', back, lang)


def admin_login(error=''):
    err=f'<div class="alert">{escape(error)}</div>' if error else ''
    html=f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Admin</title><link rel="stylesheet" href="/static/css/style.css"></head><body><main class="admin-login"><form class="form-card" method="post" action="/admin/login"><img class="admin-logo" src="/static/img/logo.png" alt=""><h1>Espace admin</h1>{err}<label>Mot de passe<input type="password" name="password" required></label><button class="btn" type="submit">Connexion</button><a class="text-link" href="/">← Retour au site</a></form></main></body></html>'''
    return html.encode()


def admin_dashboard():
    with db_connect() as conn:
        regs=conn.execute('SELECT * FROM registrations ORDER BY id DESC LIMIT 100').fetchall()
        msgs=conn.execute('SELECT * FROM messages ORDER BY id DESC LIMIT 100').fetchall()
    reg_rows=''.join(f'<tr><td>{r["id"]}</td><td>{escape(r["full_name"])}</td><td>{escape(r["email"])}</td><td>{escape(r["phone"])}</td><td>{escape(r["city"] or "")}</td><td>{escape(r["objective"] or "")}</td><td>{escape(r["created_at"])}</td></tr>' for r in regs) or '<tr><td colspan="7">Aucune inscription.</td></tr>'
    msg_rows=''.join(f'<tr><td>{r["id"]}</td><td>{escape(r["full_name"])}</td><td>{escape(r["email"])}</td><td>{escape(r["subject"] or "")}</td><td>{escape(r["message"])}</td><td>{escape(r["created_at"])}</td></tr>' for r in msgs) or '<tr><td colspan="6">Aucun message.</td></tr>'
    html=f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Admin | Viral Digitale</title><link rel="stylesheet" href="/static/css/style.css"></head><body><main class="admin-wrap"><div class="admin-top"><h1>Tableau de bord</h1><div><a class="btn btn-sm btn-ghost" href="/">Voir le site</a> <a class="btn btn-sm" href="/admin/logout">Déconnexion</a></div></div><section class="admin-section"><div class="admin-heading"><h2>Pré-inscriptions ({len(regs)})</h2><a class="text-link" href="/admin/export/inscriptions.csv">Exporter CSV</a></div><div class="table-wrap"><table><thead><tr><th>#</th><th>Nom</th><th>Email</th><th>Téléphone</th><th>Ville</th><th>Objectif</th><th>Date</th></tr></thead><tbody>{reg_rows}</tbody></table></div></section><section class="admin-section"><div class="admin-heading"><h2>Messages ({len(msgs)})</h2><a class="text-link" href="/admin/export/messages.csv">Exporter CSV</a></div><div class="table-wrap"><table><thead><tr><th>#</th><th>Nom</th><th>Email</th><th>Sujet</th><th>Message</th><th>Date</th></tr></thead><tbody>{msg_rows}</tbody></table></div></section></main></body></html>'''
    return html.encode()


class AppHandler(BaseHTTPRequestHandler):
    server_version = 'ViralDigitale/2.0'

    def log_message(self, fmt, *args):
        print(f'[{self.log_date_time_string()}] {fmt % args}')

    def send_bytes(self, body, status=200, content_type='text/html; charset=utf-8', headers=None):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'SAMEORIGIN')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        if headers:
            for k,v in headers.items(): self.send_header(k,v)
        self.end_headers(); self.wfile.write(body)

    def redirect(self, location, headers=None):
        self.send_response(303); self.send_header('Location', location)
        if headers:
            for k,v in headers.items(): self.send_header(k,v)
        self.end_headers()

    def read_form(self):
        length=int(self.headers.get('Content-Length','0') or 0)
        raw=self.rfile.read(min(length, 100_000)).decode('utf-8', errors='replace')
        data=parse_qs(raw, keep_blank_values=True)
        return {k:v[0].strip() for k,v in data.items()}

    def admin_ok(self):
        c=SimpleCookie(self.headers.get('Cookie',''))
        return valid_session(c['vd_session'].value if 'vd_session' in c else '')

    def serve_static(self, path):
        rel=path[len('/static/'):]
        file=(STATIC_DIR / rel).resolve()
        if STATIC_DIR.resolve() not in file.parents or not file.is_file():
            return self.send_bytes(b'Not found',404,'text/plain; charset=utf-8')
        mime=mimetypes.guess_type(str(file))[0] or 'application/octet-stream'
        return self.send_bytes(file.read_bytes(),200,mime,{'Cache-Control':'public, max-age=86400'})

    def do_GET(self):
        parsed=urlparse(self.path); path=parsed.path
        if path.startswith('/static/'):
            return self.serve_static(path)
        if path == '/set-lang':
            q = parse_qs(parsed.query)
            lang = q.get('lang', ['fr'])[0]
            if lang not in ('fr','ar'): lang='fr'
            nxt = q.get('next', ['/'])[0]
            if not nxt.startswith('/') or nxt.startswith('//'): nxt='/'
            return self.redirect(nxt, {'Set-Cookie':f'vd_lang={lang}; Path=/; Max-Age=31536000; SameSite=Lax'})
        lang=get_lang(self, parsed)
        if path=='/': return self.send_bytes(home_page(lang))
        if path=='/formation': return self.send_bytes(formation_page(lang))
        if path=='/programme': return self.send_bytes(programme_page(lang))
        if path=='/projets': return self.send_bytes(projets_page(lang))
        if path=='/a-propos': return self.send_bytes(about_page(lang))
        if path=='/contact': return self.send_bytes(contact_page(lang))
        if path=='/inscription': return self.send_bytes(registration_page(lang))
        if path=='/merci':
            kind=parse_qs(parsed.query).get('type',['inscription'])[0]
            return self.send_bytes(thank_you(lang, kind))
        if path=='/robots.txt':
            return self.send_bytes(b'User-agent: *\nAllow: /\nDisallow: /admin\n',200,'text/plain; charset=utf-8')
        if path=='/admin':
            return self.send_bytes(admin_dashboard() if self.admin_ok() else admin_login())
        if path=='/admin/logout':
            return self.redirect('/admin', {'Set-Cookie':'vd_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax'})
        if path.startswith('/admin/export/'):
            if not self.admin_ok(): return self.redirect('/admin')
            return self.export_csv(path)
        title = 'الصفحة غير موجودة' if lang=='ar' else 'Page introuvable'
        back = 'العودة إلى الرئيسية' if lang=='ar' else 'Retour'
        return self.send_bytes(base_page('404', f'<section class="success container"><h1>{title}</h1><a class="btn" href="/">{back}</a></section>', path, lang),404)

    def do_POST(self):
        parsed=urlparse(self.path); path=parsed.path; data=self.read_form(); lang=get_lang(self, parsed)
        if path=='/inscription':
            required=['full_name','email','phone']
            if any(not data.get(k) for k in required):
                msg='يرجى ملء الحقول الإجبارية.' if lang=='ar' else 'Merci de remplir les champs obligatoires.'
                return self.send_bytes(error_page(lang,msg,'/inscription'),400)
            with db_connect() as conn:
                conn.execute('INSERT INTO registrations(full_name,email,phone,city,objective,created_at) VALUES(?,?,?,?,?,?)',(data['full_name'][:100],data['email'][:120],data['phone'][:30],data.get('city','')[:80],data.get('objective','')[:120],datetime.now().strftime('%Y-%m-%d %H:%M')))
            return self.redirect('/merci?type=inscription')
        if path=='/contact':
            if not data.get('full_name') or not data.get('email') or not data.get('message'):
                msg='يرجى ملء الحقول الإجبارية.' if lang=='ar' else 'Merci de remplir les champs obligatoires.'
                return self.send_bytes(error_page(lang,msg,'/contact'),400)
            with db_connect() as conn:
                conn.execute('INSERT INTO messages(full_name,email,subject,message,created_at) VALUES(?,?,?,?,?)',(data['full_name'][:100],data['email'][:120],data.get('subject','')[:140],data['message'][:1500],datetime.now().strftime('%Y-%m-%d %H:%M')))
            return self.redirect('/merci?type=contact')
        if path=='/admin/login':
            if hmac.compare_digest(data.get('password',''), ADMIN_PASSWORD):
                cookie=make_session()
                return self.redirect('/admin', {'Set-Cookie':f'vd_session={cookie}; Path=/; HttpOnly; SameSite=Lax'})
            return self.send_bytes(admin_login('Mot de passe incorrect.'),401)
        return self.send_bytes(b'Not found',404,'text/plain; charset=utf-8')

    def export_csv(self, path):
        if path.endswith('inscriptions.csv'):
            table='registrations'; cols=['id','full_name','email','phone','city','objective','created_at']; filename='inscriptions.csv'
        elif path.endswith('messages.csv'):
            table='messages'; cols=['id','full_name','email','subject','message','created_at']; filename='messages.csv'
        else: return self.send_bytes(b'Not found',404,'text/plain')
        with db_connect() as conn: rows=conn.execute(f'SELECT * FROM {table} ORDER BY id DESC').fetchall()
        s=io.StringIO(); w=csv.writer(s); w.writerow(cols)
        for r in rows: w.writerow([r[c] for c in cols])
        b=s.getvalue().encode('utf-8-sig')
        return self.send_bytes(b,200,'text/csv; charset=utf-8',{'Content-Disposition':f'attachment; filename="{filename}"'})


if __name__=='__main__':
    init_db()
    print(f'Viral Digitale Academy running on http://{HOST}:{PORT}')
    print('Bilingual site: Français / العربية')
    print('Admin: /admin  | Default password: viral2026 (change with ADMIN_PASSWORD env var)')
    ThreadingHTTPServer((HOST, PORT), AppHandler).serve_forever()
