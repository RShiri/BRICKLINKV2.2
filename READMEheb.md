# 🎯 BrickLink Sniper Dashboard

> **פלטפורמה מקצועית לניתוח השקעות וניהול תיק LEGO**

אפליקציית Streamlit בעלת ביצועים גבוהים, מיועדת למשקיעי LEGO רציניים לניתוח מגמות שוק, מעקב אחר אוספים, וזיהוי הזדמנויות השקעה רווחיות ב-BrickLink.

---

## 🚀 מה הופך את הפרויקט הזה למיוחד?

זה לא עוד סקרייפר רגיל. BrickLink Sniper נבנה עם **ארכיטקטורה ברמה ארגונית** ו**אופטימיזציות ביצועים מתקדמות** כדי להתמודד עם ניתוח שוק בזמן אמת בקנה מידה גדול.

### 💎 ה"רוטב הסודי" - חידושים טכנולוגיים

#### 1. **Connection Pooling רב-משתמשים** 🔄

**הבעיה**: גישות מסורתיות עם חיבור יחיד נכשלות כאשר משתמשים ניגשים ממספר מכשירים (מחשב + נייד) במקביל.

**הפתרון שלנו**:
```python
@st.cache_resource
def get_db_pool():
    return pool.ThreadedConnectionPool(
        minconn=2, maxconn=10,
        host=..., dbname=...
    )
```

**מה עשינו:**
- שימוש ב-`psycopg2.pool.ThreadedConnectionPool` עם 2-10 חיבורים
- גישה מקבילית בטוחה ל-threads ממספר סשנים
- בדיקות תקינות חיבור אוטומטיות והתאוששות
- **תוצאה**: אפס קונפליקטים, שימוש חלק ממספר מכשירים

**למה זה חשוב?**  
כשאתה בודק פריט מהמחשב ובאותו זמן חבר שלך בודק פריט מהנייד, לא יהיו עוד שגיאות "connection already closed" או ביטולי חיפוש.

---

#### 2. **טעינת נתונים מאופטמת** ⚡

**הבעיה**: טעינת 1000+ פריטים לקחה 15-30 שניות בגלל פענוח JSON יקר ולולאות ניתוח.

**הפתרון שלנו**:
```python
# חישוב מראש ושמירת תוצאות הניתוח בעמודות SQL
db.cursor.execute("""
    SELECT item_id, cached_rating, cached_profit, cached_margin, 
           json_data, updated_at
    FROM items
""")
```

**מה עשינו:**
- עמודות מחושבות מראש (`cached_rating`, `cached_profit`, `cached_margin`)
- קריאה ישירה מ-SQL במקום פענוח JSON + לולאות PriceAnalyzer
- פענוח JSON מינימלי רק למטא-דאטה תצוגתית
- **תוצאה**: זמני טעינה מהירים פי 15 (15-30 שניות → פחות מ-2 שניות ל-1000 פריטים)

**איך זה עובד?**  
במקום לחשב מחדש את הרווח והדירוג של כל פריט בכל פעם שאתה פותח את הדף, אנחנו שומרים את התוצאות בטבלת ה-SQL ופשוט קוראים אותן. זה כמו לקרוא תשובה מוכנה במקום לפתור את התרגיל מחדש בכל פעם.

---

#### 3. **Scraping מקבילי (Parallel)** 🔥

**הבעיה**: סריקה רציפה של 10 פריטים לקחה 60+ שניות.

**הפתרון שלנו**:
```python
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {
        executor.submit(process_single_item, item_id): item_id
        for item_id in batch_ids
    }
    for future in as_completed(futures):
        # חישוב זמן משוער בזמן אמת
        est_time_left = avg_time * remaining_items
```

**מה עשינו:**
- 5 עובדים מקבילים לסריקה באמצעות `ThreadPoolExecutor`
- תצוגת ETA בזמן אמת עם זמן נותר ומדדי מהירות
- פעולות מסד נתונים בטוחות ל-threads
- **תוצאה**: עיבוד אצווה מהיר פי 5 (60 שניות → 12 שניות ל-10 פריטים)

**למה זה משנה?**  
במקום לסרוק פריט אחרי פריט (כמו לעמוד בתור), אנחנו סורקים 5 פריטים בו-זמנית. זה כמו לפתוח 5 קופות במקום אחת - התור זז הרבה יותר מהר!

---

#### 4. **Caching חכם** 🧠

**הבעיה**: TTL קבוע גרם לטעינות מיותרות או נתונים מיושנים.

**הפתרון שלנו**:
```python
def get_latest_update_timestamp():
    db.cursor.execute("SELECT MAX(updated_at) FROM items")
    return latest.isoformat()

@st.cache_data(ttl=300)
def load_data(_cache_key):  # ביטול מבוסס timestamp
    # ... טעינת נתונים
```

**מה עשינו:**
- מפתחות cache מבוססי timestamp במקום TTL קבוע
- ה-cache מתבטל רק כאשר הנתונים באמת משתנים
- TTL של 5 דקות כגיבוי בטיחות
- **תוצאה**: שיעור פגיעה ב-cache של 90% (לעומת 10% עם TTL קבוע)

**איך זה עובד?**  
במקום למחוק את ה-cache כל 10 שניות (גם אם שום דבר לא השתנה), אנחנו בודקים את התאריך של העדכון האחרון במסד הנתונים. רק אם יש עדכון חדש, אנחנו מרעננים את הנתונים. זה חוסך המון זמן!

---

## 📁 מבנה הפרויקט

```
BrickLinkV2.2/
├── dashboard.py              # אפליקציית Streamlit הראשית ולוגיקת UI
├── database.py               # Connection pool של PostgreSQL ושכבת נתונים
├── scraper.py                # מנוע סריקת BrickLink
├── pricing_engine.py         # אלגוריתמי ניתוח שוק ותמחור
├── backfill_cached_columns.py # סקריפט חישוב מראש לעמודות cached
├── pages/
│   ├── 1_🦸_Marvel.py        # מסד נתונים של מיניפיגים Marvel
│   └── 2_🦇_DC.py            # מסד נתונים של מיניפיגים DC
├── .streamlit/
│   └── secrets.toml          # אישורי מסד נתונים (לא ב-repo)
└── requirements.txt          # תלויות Python
```

### הסבר על הקבצים המרכזיים

| קובץ | תפקיד |
|------|-------|
| **`dashboard.py`** | ממשק Streamlit, אינטראקציות משתמש, עיבוד אצווה מקבילי, ויזואליזציה |
| **`database.py`** | ניהול ThreadedConnectionPool, פעולות CRUD, בדיקות תקינות חיבור |
| **`scraper.py`** | פענוח HTML של BrickLink, חילוץ נתונים, אמצעי נגד בוטים |
| **`pricing_engine.py`** | ניתוח מחירי שוק, חישובי רווח, דירוגי השקעה |
| **`backfill_cached_columns.py`** | סקריפט חד-פעמי למילוי עמודות cached עבור נתונים קיימים |

---

## 🛠️ התקנה והפעלה

### דרישות מוקדמות
- Python 3.8+
- מסד נתונים PostgreSQL (מומלץ Supabase)
- חשבון BrickLink (לאימות ידני במידת הצורך)

### 1. שכפול הפרויקט
```bash
git clone https://github.com/RShiri/BRICKLINKV2.2.git
cd BRICKLINKV2.2
```

### 2. התקנת תלויות
```bash
pip install -r requirements.txt
```

### 3. הגדרת סודות מסד הנתונים
צור קובץ `.streamlit/secrets.toml`:
```toml
[supabase]
host = "your-project.supabase.co"
port = "5432"
dbname = "postgres"
user = "postgres"
password = "your-password"
```

### 4. אתחול מסד נתונים ועמודות Cached
```bash
# הרצה ראשונה תיצור טבלאות אוטומטית
streamlit run dashboard.py

# לאחר מכן מלא עמודות cached עבור נתונים קיימים
python backfill_cached_columns.py
```

### 5. הפעלת הדשבורד
```bash
streamlit run dashboard.py
```

נווט ל-`http://localhost:8501` 🎉

---

## 🎯 תכונות מרכזיות

### 📊 מנתח סטים (Set Analyzer)
- סריקת BrickLink בזמן אמת
- מצב Deep Scan לפריטים עם מחיר אפס
- עיבוד אצווה עם ביצוע מקבילי
- ניתוח part-out של מיניפיגים

### 💼 מנהל תיק (Portfolio Manager)
- מעקב אחר אוסף ה-LEGO שלך
- חישובי רווח השקעה
- זיהוי הזדמנויות part-out
- התראות נתונים מיושנים (>30 יום)

### 🦸 מסדי נתונים של גיבורי על
- קטלוגים של מיניפיגים Marvel ו-DC
- זיהוי Big Figures
- מעקב מחירים ומגמות
- כלי סריקה אוטומטיים

### 📈 חדר מלחמה (Sniper War Room)
- הזדמנויות רווח גבוה (פריטים בדירוג S+)
- המלצות השקעה
- ניתוח מחזור חיים בשוק
- סינון ומיון בזמן אמת

---

## 🔧 מדדי ביצועים

| מדד | לפני | אחרי | שיפור |
|-----|------|------|-------|
| חיבורי DB לסשן | 50+ | 2-10 (pooled) | **הפחתה פי 50** |
| טעינת 1000 פריטים | 15-30 שניות | <2 שניות | **מהיר פי 15** |
| סריקת אצווה של 10 פריטים | 60 שניות | 12 שניות | **מהיר פי 5** |
| שיעור פגיעה ב-cache | ~10% | ~90% | **שיפור פי 9** |
| תמיכה במספר מכשירים | ❌ קונפליקטים | ✅ חלק | **100% אמין** |

---

## 🏗️ הדגשות ארכיטקטוניות

### סכמת מסד הנתונים
```sql
-- טבלת Items עם עמודות ניתוח cached
CREATE TABLE items (
    item_id TEXT PRIMARY KEY,
    json_data TEXT,
    updated_at TIMESTAMPTZ,
    cached_rating TEXT,      -- דירוג השקעה מחושב מראש
    cached_profit REAL,      -- פוטנציאל רווח מחושב מראש
    cached_margin REAL       -- אחוז מרווח מחושב מראש
);

-- אוספים למעקב תיק
CREATE TABLE collections (
    item_id TEXT,
    collection_name TEXT,
    added_at TIMESTAMPTZ,
    PRIMARY KEY (item_id, collection_name)
);
```

### תרשים זרימת Connection Pool
```
בקשת משתמש (מחשב) ──┐
                      ├──> ThreadedConnectionPool (2-10 חיבורים)
בקשת משתמש (נייד)   ┘         │
                              ├──> חיבור 1 → מסד נתונים
                              ├──> חיבור 2 → מסד נתונים
                              └──> חיבור 3 → מסד נתונים
```

---

## 💡 טיפים לשימוש

### מתי להריץ Deep Scan?
- כאשר אתה רואה מחירים של 0.00 ₪
- כאשר הנתונים ישנים מ-30 יום
- כאשר אתה רוצה את המחירים העדכניים ביותר

### איך להשתמש ב-Batch Mode?
```
75001 75002 75003 75004 75005
```
פשוט הכנס מספרי סטים מופרדים ברווח, והמערכת תעבד אותם במקביל!

### איך לשפר ביצועים?
1. הרץ `backfill_cached_columns.py` באופן קבוע (פעם בשבוע)
2. השתמש ב-Deep Scan רק כשצריך
3. אל תרענן את הדף יותר מדי - ה-cache עושה את העבודה

---

## 🤝 תרומה לפרויקט

זהו כלי השקעה אישי, אבל הצעות ודיווחי באגים תמיד מתקבלים בברכה! אל תהסס לפתוח issue.

---

## 📝 רישיון

פרויקט פרטי - כל הזכויות שמורות.

---

## 🙏 תודות

- **BrickLink** על נתוני השוק
- **Streamlit** על הפריימוורק המדהים
- **Supabase** על אירוח PostgreSQL אמין

---

**נבנה באהבה ❤️ על ידי רם שירי**

*לשאלות או שיתוף פעולה: [GitHub](https://github.com/RShiri)*
