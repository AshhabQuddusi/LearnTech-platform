
import sqlite3, hashlib, os
from flask import (Flask, render_template, request,
                   jsonify, session, redirect, url_for, g)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "learntech-arcade-key-change-in-prod")
DB_PATH = os.path.join(os.path.dirname(__file__), "learntech.db")


# ─────────────────────────────────────────────
# DATABASE HELPERS
# ─────────────────────────────────────────────

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db

@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db: db.close()

def query(sql, params=(), one=False):
    cur = get_db().execute(sql, params)
    return cur.fetchone() if one else cur.fetchall()

def execute(sql, params=()):
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    return cur.lastrowid


# ─────────────────────────────────────────────
# SCHEMA
# ─────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    email      TEXT NOT NULL UNIQUE,
    password   TEXT NOT NULL,
    is_premium INTEGER DEFAULT 0,
    total_xp   INTEGER DEFAULT 50,
    level      INTEGER DEFAULT 1,
    joined_at  TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS courses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT,
    category    TEXT,
    level       TEXT,
    source      TEXT,
    url         TEXT,
    is_premium  INTEGER DEFAULT 0,
    created_at  TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS articles (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT NOT NULL,
    summary    TEXT,
    category   TEXT,
    tags       TEXT,
    source     TEXT,
    url        TEXT,
    is_premium INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS xp_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    source     TEXT,
    xp         INTEGER DEFAULT 0,
    note       TEXT,
    earned_at  TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS contact_messages (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT,
    email   TEXT,
    message TEXT,
    sent_at TEXT DEFAULT (datetime('now'))
);
"""


# ─────────────────────────────────────────────
# SEED DATA  —  35 real, free, open-source courses
# Format: (title, description, category, level, source, url, is_premium)
# ─────────────────────────────────────────────

SEED_COURSES = [

    # ══════════════════ WEB DEVELOPMENT ══════════════════
    (
        "Responsive Web Design",
        "Learn HTML5 and CSS3 by building 15 real projects — cat photo apps, nutrition labels, "
        "Picasso paintings. 300 hours of content, free certification included.",
        "web", "beginner", "freeCodeCamp",
        "https://www.freecodecamp.org/learn/2022/responsive-web-design/", 0
    ),
    (
        "JavaScript Algorithms & Data Structures",
        "ES6, regex, debugging, data structures, OOP, and functional programming. "
        "Earn a free JavaScript certification from freeCodeCamp.",
        "web", "beginner", "freeCodeCamp",
        "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/", 0
    ),
    (
        "The Odin Project — Full Stack JavaScript",
        "The most complete free full-stack curriculum on the internet. "
        "HTML, CSS, JavaScript, Node, React, and databases — with real projects.",
        "web", "beginner", "The Odin Project",
        "https://www.theodinproject.com/paths/full-stack-javascript", 0
    ),
    (
        "Front End Development Libraries",
        "Bootstrap, jQuery, Sass, React, and Redux — all in one free certification path. "
        "Build a 25+5 Clock, Drum Machine, and Markdown Previewer.",
        "web", "intermediate", "freeCodeCamp",
        "https://www.freecodecamp.org/learn/front-end-development-libraries/", 0
    ),
    (
        "Full Stack Open 2024",
        "University of Helsinki's modern web dev course. React, Node, GraphQL, TypeScript, "
        "CI/CD, containers. Free to take, option to earn university credits.",
        "web", "intermediate", "University of Helsinki",
        "https://fullstackopen.com/en/", 0
    ),
    (
        "JavaScript30",
        "Build 30 things in 30 days with vanilla JavaScript. "
        "No frameworks, no compilers, no libraries — just pure JS.",
        "web", "beginner", "Wes Bos",
        "https://javascript30.com/", 0
    ),
    (
        "Web Dev For Beginners",
        "Microsoft's 12-week, 24-lesson curriculum on JavaScript, CSS, and HTML basics. "
        "Project-based with quizzes, lectures, and videos.",
        "web", "beginner", "Microsoft",
        "https://microsoft.github.io/Web-Dev-For-Beginners/", 0
    ),
    (
        "CSS Grid",
        "Wes Bos's free video course teaching CSS Grid from scratch. "
        "25 videos covering every part of the spec with real layouts.",
        "web", "beginner", "Wes Bos",
        "https://cssgrid.io/", 0
    ),

    # ══════════════════ PYTHON ══════════════════
    (
        "Python for Everybody",
        "Dr. Chuck's world-famous Python course from University of Michigan. "
        "Data, files, web scraping, SQL databases, and data visualisation. Millions enrolled.",
        "python", "beginner", "University of Michigan",
        "https://www.py4e.com/", 0
    ),
    (
        "Automate the Boring Stuff with Python",
        "The most practical Python book online — completely free to read. "
        "PDF manipulation, web scraping, Excel automation, email scheduling, and more.",
        "python", "beginner", "Al Sweigart",
        "https://automatetheboringstuff.com/", 0
    ),
    (
        "Scientific Computing with Python",
        "freeCodeCamp's Python certification. Covers arithmetic, strings, loops, "
        "data structures, and five real projects including a budget app.",
        "python", "beginner", "freeCodeCamp",
        "https://www.freecodecamp.org/learn/scientific-computing-with-python/", 0
    ),
    (
        "Google's Python Class",
        "A free Python class for people with some programming experience. "
        "Written by Google engineers, includes lecture videos and exercises.",
        "python", "beginner", "Google",
        "https://developers.google.com/edu/python", 0
    ),
    (
        "Python Programming MOOC 2024",
        "University of Helsinki's two-part Python course — Introduction and Advanced. "
        "Highly rated, project-based, completely free with optional credits.",
        "python", "beginner", "University of Helsinki",
        "https://programming-24.mooc.fi/", 0
    ),
    (
        "Practical Python Programming",
        "David Beazley's Python course taught to scientists, engineers, and programmers. "
        "Covers all the core Python language features through practical exercises.",
        "python", "intermediate", "David Beazley",
        "https://dabeaz-course.github.io/practical-python/", 0
    ),

    # ══════════════════ DATA SCIENCE & ML ══════════════════
    (
        "Data Analysis with Python",
        "NumPy, Pandas, Matplotlib, and Seaborn — all free. "
        "Build a demographic data analyser and medical data visualiser as projects.",
        "data", "intermediate", "freeCodeCamp",
        "https://www.freecodecamp.org/learn/data-analysis-with-python/", 0
    ),
    (
        "Machine Learning with Python",
        "Regression, classification, neural nets with TensorFlow 2. "
        "Build a Rock Paper Scissors AI, book recommendation engine, and health cost calculator.",
        "data", "intermediate", "freeCodeCamp",
        "https://www.freecodecamp.org/learn/machine-learning-with-python/", 0
    ),
    (
        "fast.ai — Practical Deep Learning",
        "Top-down, code-first deep learning used by professionals worldwide. "
        "Computer vision, NLP, tabular data — all with PyTorch. Completely free.",
        "data", "advanced", "fast.ai",
        "https://course.fast.ai/", 0
    ),
    (
        "CS50's Introduction to AI with Python",
        "Harvard's AI course — search algorithms, knowledge, uncertainty, "
        "optimisation, machine learning, neural networks, and natural language.",
        "data", "intermediate", "Harvard CS50",
        "https://cs50.harvard.edu/ai/2024/", 0
    ),
    (
        "Kaggle — Intro to Machine Learning",
        "Build your first ML model in under an hour. "
        "Free interactive micro-course in your browser — no setup needed.",
        "data", "beginner", "Kaggle",
        "https://www.kaggle.com/learn/intro-to-machine-learning", 0
    ),
    (
        "Kaggle — Python",
        "Free Python micro-course covering lists, loops, functions, "
        "and external libraries — all interactive in your browser.",
        "data", "beginner", "Kaggle",
        "https://www.kaggle.com/learn/python", 0
    ),
    (
        "Elements of AI",
        "The University of Helsinki and Reaktor's AI course for non-programmers. "
        "Over 750,000 people have completed it. Free with optional ECTS credits.",
        "data", "beginner", "University of Helsinki",
        "https://www.elementsofai.com/", 0
    ),

    # ══════════════════ BACKEND & CS ══════════════════
    (
        "CS50: Introduction to Computer Science",
        "Harvard's most popular course — ever. C, Python, SQL, HTML/CSS/JS. "
        "Problem sets that challenge you. Free certificate from edX available.",
        "backend", "beginner", "Harvard CS50",
        "https://cs50.harvard.edu/x/", 0
    ),
    (
        "CS50's Web Programming with Python & JavaScript",
        "Django, SQL, JavaScript, Git, and CI/CD. "
        "Harvard's follow-up to CS50 focused entirely on full-stack web development.",
        "backend", "intermediate", "Harvard CS50",
        "https://cs50.harvard.edu/web/2020/", 0
    ),
    (
        "Back End Development & APIs",
        "Node.js, Express, MongoDB, and Mongoose — build a full microservices project. "
        "freeCodeCamp's backend certification path.",
        "backend", "intermediate", "freeCodeCamp",
        "https://www.freecodecamp.org/learn/back-end-development-and-apis/", 0
    ),
    (
        "Relational Databases",
        "SQL from scratch using PostgreSQL in a real Linux environment. "
        "Build a Celestial Bodies Database, Number Guessing Game, and more.",
        "backend", "beginner", "freeCodeCamp",
        "https://www.freecodecamp.org/learn/relational-database/", 0
    ),
    (
        "Introduction to Algorithms — MIT OCW",
        "MIT 6.006 — the gold standard algorithms course. Lecture notes, "
        "problem sets, exams, and solutions. Completely free online.",
        "backend", "advanced", "MIT OpenCourseWare",
        "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/", 0
    ),
    (
        "Nand to Tetris",
        "Build a modern computer from first principles — logic gates to OS. "
        "One of the most unique CS courses online. Free on Coursera audit.",
        "backend", "intermediate", "Hebrew University",
        "https://www.nand2tetris.org/", 0
    ),

    # ══════════════════ TOOLS & SECURITY ══════════════════
    (
        "The Missing Semester of Your CS Education",
        "MIT's course on the tools school never taught you: "
        "shell, Vim, Git, debugging, profiling, and security. Free lecture videos.",
        "tools", "beginner", "MIT",
        "https://missing.csail.mit.edu/", 0
    ),
    (
        "Linux Command Line Basics",
        "Terminal, file system, permissions, pipes, grep, shell scripting, "
        "and cron jobs. Everything you need to work confidently on any server.",
        "tools", "beginner", "Ryan Chadwick",
        "https://ryanstutorials.net/linuxtutorial/", 0
    ),
    (
        "Git Immersion",
        "A guided tour through the fundamentals of Git. "
        "Hands-on exercises you run in your own terminal. Free, no sign-up needed.",
        "tools", "beginner", "Neo / Jim Weirich",
        "https://gitimmersion.com/", 0
    ),
    (
        "Information Security",
        "Penetration testing, cryptography, Kali Linux, and Metasploit. "
        "Earn certs in partnership with freeCodeCamp. Advanced but free.",
        "tools", "advanced", "freeCodeCamp",
        "https://www.freecodecamp.org/learn/information-security/", 0
    ),
    (
        "SQL Murder Mystery",
        "Learn SQL by solving a murder mystery — write queries to find the culprit. "
        "The most fun way to learn databases. Completely free.",
        "data", "beginner", "Knight Lab",
        "https://mystery.knightlab.com/", 0
    ),
    (
        "Regex One",
        "Learn regular expressions with simple, interactive exercises. "
        "15 lessons covering every aspect of regex — free, no login required.",
        "tools", "beginner", "RegexOne",
        "https://regexone.com/", 0
    ),
    (
        "CS50's Introduction to Cybersecurity",
        "Harvard's cybersecurity course — how defenders and attackers think. "
        "Covers phishing, passwords, malware, and safe coding. Free.",
        "tools", "beginner", "Harvard CS50",
        "https://cs50.harvard.edu/cybersecurity/2023/", 0
    ),

]


SEED_ARTICLES = [
    ("MDN — HTML Reference", "Every HTML element and attribute, fully documented.", "docs", "html,reference,web", "MDN", "https://developer.mozilla.org/en-US/docs/Web/HTML", 0),
    ("MDN — CSS Reference", "Every CSS property, selector, and value documented.", "docs", "css,reference,web", "MDN", "https://developer.mozilla.org/en-US/docs/Web/CSS", 0),
    ("MDN — JavaScript Reference", "Complete JS language reference — objects, methods, operators.", "docs", "javascript,reference,web", "MDN", "https://developer.mozilla.org/en-US/docs/Web/JavaScript", 0),
    ("The Odin Project — Full Stack Path", "A free open-source curriculum from zero to full-stack developer.", "guide", "fullstack,html,css,js", "The Odin Project", "https://www.theodinproject.com", 0),
    ("CS50 — Intro to Computer Science", "Harvard's legendary intro CS course. Free, online, world-class.", "course", "cs,python,c,algorithms,harvard", "Harvard CS50", "https://cs50.harvard.edu/x/", 0),
    ("Python Official Documentation", "The authoritative Python 3 reference — tutorials and library docs.", "docs", "python,reference,stdlib", "Python.org", "https://docs.python.org/3/", 0),
    ("Pro Git Book", "The entire Git book by Chacon & Straub — free online.", "book", "git,version-control,tools", "Apress", "https://git-scm.com/book/en/v2", 0),
    ("System Design Primer", "How to design large-scale systems. GitHub's most-starred CS resource.", "guide", "system-design,backend,architecture", "GitHub", "https://github.com/donnemartin/system-design-primer", 0),
    ("Attention Is All You Need", "The 2017 Transformer paper — essential ML reading.", "paper", "ml,transformers,nlp,research", "arXiv", "https://arxiv.org/abs/1706.03762", 0),
    ("Automate the Boring Stuff — Book", "Al Sweigart's Python automation book, free to read online.", "book", "python,automation,scripting,beginner", "Al Sweigart", "https://automatetheboringstuff.com/", 0),
    ("Full Stack Open Curriculum", "React, Node, GraphQL, TypeScript — free with university credits.", "guide", "react,node,fullstack,typescript", "U. Helsinki", "https://fullstackopen.com/en/", 0),
    ("fast.ai — Practical Deep Learning", "Code-first deep learning — vision, NLP, tabular, PyTorch.", "course", "ml,deeplearning,pytorch,ai", "fast.ai", "https://course.fast.ai/", 0),
    ("Kaggle — Python Micro-Course", "Free interactive Python in your browser, no setup needed.", "course", "python,beginner,interactive", "Kaggle", "https://www.kaggle.com/learn/python", 0),
    ("CSS Tricks — Complete Guide to Grid", "The definitive visual guide to CSS Grid — bookmark this forever.", "article", "css,grid,layout,web", "CSS-Tricks", "https://css-tricks.com/snippets/css/complete-guide-grid/", 0),
    ("The Missing Semester — Shell Tools", "MIT's deep-dive on shell, grep, sed, awk, and scripting.", "guide", "linux,shell,tools,scripting", "MIT", "https://missing.csail.mit.edu/2020/shell-tools/", 0),
    ("MIT OCW — Introduction to Algorithms", "MIT 6.006 lecture notes, problem sets, exams — free.", "course", "algorithms,data-structures,mit,cs", "MIT OCW", "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/", 0),
    ("Elements of AI", "Helsinki & Reaktor's AI course for non-programmers. 750k+ completions.", "course", "ai,beginners,concepts,ml", "U. Helsinki", "https://www.elementsofai.com/", 0),
    ("SQL Murder Mystery", "Learn SQL by solving an interactive murder mystery. Free, no login.", "guide", "sql,databases,interactive,beginner", "Knight Lab", "https://mystery.knightlab.com/", 0),
    ("Git Immersion", "Guided hands-on tour through Git fundamentals — in your own terminal.", "guide", "git,version-control,terminal,tools", "Neo", "https://gitimmersion.com/", 0),
    ("Nand to Tetris", "Build a computer from first principles — logic gates to OS.", "course", "cs,hardware,architecture,advanced", "Hebrew University", "https://www.nand2tetris.org/", 0),
]


# ─────────────────────────────────────────────
# DB INIT — auto-reseeds stale / placeholder data
# ─────────────────────────────────────────────

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    db.commit()

    total       = db.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    placeholder = db.execute("SELECT COUNT(*) FROM courses WHERE url='#' OR url=''").fetchone()[0]
    old_title   = db.execute("SELECT COUNT(*) FROM courses WHERE title='HTML5 for Beginners'").fetchone()[0]

    # Reseed if DB is empty, has placeholder URLs, has old seed data, or too few courses
    if total == 0 or placeholder > 0 or old_title > 0 or total < 20:
        print(f"  Reseeding database (had {total} courses, {placeholder} placeholders)…")
        db.execute("DELETE FROM courses")
        db.execute("DELETE FROM articles")
        db.commit()
        db.executemany(
            "INSERT INTO courses (title,description,category,level,source,url,is_premium) VALUES (?,?,?,?,?,?,?)",
            SEED_COURSES)
        db.executemany(
            "INSERT INTO articles (title,summary,category,tags,source,url,is_premium) VALUES (?,?,?,?,?,?,?)",
            SEED_ARTICLES)
        db.commit()
        print(f"  ✓ Seeded {len(SEED_COURSES)} courses, {len(SEED_ARTICLES)} articles")
    else:
        print(f"  ✓ Database OK — {total} courses, {db.execute('SELECT COUNT(*) FROM articles').fetchone()[0]} articles")

    db.close()


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def hash_pw(raw):
    return hashlib.sha256(raw.encode()).hexdigest()

def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    row = query("SELECT * FROM users WHERE id=?", (uid,), one=True)
    return dict(row) if row else None

def calc_level(xp):
    return max(1, xp // 500 + 1)

def award_xp(user_id, amount, source="general", note=""):
    execute("INSERT INTO xp_events (user_id,source,xp,note) VALUES (?,?,?,?)",
            (user_id, source, amount, note))
    current_xp = query("SELECT total_xp FROM users WHERE id=?", (user_id,), one=True)["total_xp"]
    execute("UPDATE users SET total_xp=?, level=? WHERE id=?",
            (current_xp + amount, calc_level(current_xp + amount), user_id))


# ─────────────────────────────────────────────
# PAGE ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def home():
    courses = [dict(r) for r in query("SELECT * FROM courses LIMIT 3")]
    return render_template("index.html", courses=courses, user=current_user())

@app.route("/courses")
def courses():
    return render_template("courses.html", user=current_user())

@app.route("/stack")
def stack():
    return render_template("stack.html", user=current_user())

@app.route("/learntech")
def learntech():
    return render_template("learntech.html", user=current_user())

@app.route("/premium")
def premium():
    return render_template("premium.html", user=current_user())

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json()
        user = query("SELECT * FROM users WHERE email=?", (data.get("email", ""),), one=True)
        if user and user["password"] == hash_pw(data.get("password", "")):
            session["user_id"] = user["id"]
            return jsonify({"ok": True, "name": user["name"], "premium": bool(user["is_premium"])})
        return jsonify({"ok": False, "error": "Wrong email or password"}), 401
    return render_template("login.html", user=None)

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if query("SELECT id FROM users WHERE email=?", (data.get("email", ""),), one=True):
        return jsonify({"ok": False, "error": "Email already registered"}), 400
    uid = execute(
        "INSERT INTO users (name,email,password,total_xp) VALUES (?,?,?,?)",
        (data.get("name", ""), data.get("email", ""), hash_pw(data.get("password", "")), 50)
    )
    execute("INSERT INTO xp_events (user_id,source,xp,note) VALUES (?,?,?,?)",
            (uid, "register", 50, "Welcome bonus!"))
    session["user_id"] = uid
    return jsonify({"ok": True, "name": data.get("name", ""), "xp": 50})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=user)


# ─────────────────────────────────────────────
# JSON API
# ─────────────────────────────────────────────

@app.route("/api/courses")
def api_courses():
    cat   = request.args.get("cat",   "").strip()
    level = request.args.get("level", "").strip()
    sql   = "SELECT * FROM courses WHERE 1=1"
    params = []
    if cat:   sql += " AND category=?"; params.append(cat)
    if level: sql += " AND level=?";    params.append(level)
    sql += " ORDER BY id"
    rows = query(sql, params)
    return jsonify([dict(r) for r in rows])

@app.route("/api/stack")
def api_stack():
    cat = request.args.get("cat", "").strip()
    sql = "SELECT * FROM articles WHERE 1=1"
    params = []
    if cat: sql += " AND category=?"; params.append(cat)
    sql += " ORDER BY id"
    result = []
    for a in query(sql, params):
        d = dict(a)
        d["tags"] = [t.strip() for t in (d.get("tags") or "").split(",") if t.strip()]
        result.append(d)
    return jsonify(result)

@app.route("/api/search")
def api_search():
    q     = request.args.get("q", "").lower().strip()
    limit = min(int(request.args.get("limit", 20)), 50)
    if not q:
        return jsonify([])
    results, term = [], f"%{q}%"
    for c in query(
        "SELECT * FROM courses WHERE lower(title) LIKE ? OR lower(description) LIKE ? OR lower(category) LIKE ?",
        (term, term, term)
    ):
        results.append({"type": "course", "title": c["title"], "summary": c["description"] or "",
                        "source": c["source"] or "", "url": c["url"] or "#",
                        "tags": [c["category"], c["level"]], "premium": bool(c["is_premium"])})
    for a in query(
        "SELECT * FROM articles WHERE lower(title) LIKE ? OR lower(summary) LIKE ? OR lower(tags) LIKE ?",
        (term, term, term)
    ):
        results.append({"type": a["category"] or "article", "title": a["title"],
                        "summary": a["summary"] or "", "source": a["source"] or "",
                        "url": a["url"] or "#", "tags": (a["tags"] or "").split(","),
                        "premium": bool(a["is_premium"])})
    return jsonify(results[:limit])

@app.route("/api/contact", methods=["POST"])
def api_contact():
    data = request.get_json()
    execute("INSERT INTO contact_messages (name,email,message) VALUES (?,?,?)",
            (data.get("name", ""), data.get("email", ""), data.get("message", "")))
    return jsonify({"ok": True})

@app.route("/api/stats")
def api_stats():
    return jsonify({
        "students": query("SELECT COUNT(*) as c FROM users", one=True)["c"] + 82000,
        "courses":  query("SELECT COUNT(*) as c FROM courses", one=True)["c"],
        "articles": query("SELECT COUNT(*) as c FROM articles", one=True)["c"],
        "premium":  query("SELECT COUNT(*) as c FROM users WHERE is_premium=1", one=True)["c"],
    })

@app.route("/api/xp/award", methods=["POST"])
def api_award_xp():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    data   = request.get_json()
    amount = min(int(data.get("amount", 10)), 500)
    award_xp(uid, amount, data.get("source", "action"), data.get("note", ""))
    user = query("SELECT total_xp, level FROM users WHERE id=?", (uid,), one=True)
    return jsonify({"ok": True, "total_xp": user["total_xp"], "level": user["level"]})

@app.route("/api/me")
def api_me():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"ok": False}), 401
    user = query("SELECT id,name,is_premium,total_xp,level,joined_at FROM users WHERE id=?", (uid,), one=True)
    history = [dict(r) for r in query(
        "SELECT source,xp,note,earned_at FROM xp_events WHERE user_id=? ORDER BY earned_at DESC LIMIT 10",
        (uid,))]
    return jsonify({**dict(user), "xp_history": history})

@app.route("/api/leaderboard")
def api_leaderboard():
    rows = query("SELECT name, total_xp, level FROM users ORDER BY total_xp DESC LIMIT 20")
    return jsonify([dict(r) for r in rows])


# ─────────────────────────────────────────────
# ERROR HANDLERS
# ─────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html", user=current_user()), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("404.html", user=current_user()), 500


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("LearnTech Arcade — starting up…")
    init_db()
    print("✓ Ready → http://localhost:5000")
    app.run(debug=True, port=5000)
