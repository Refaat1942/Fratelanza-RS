# Fratelanza Demo — Quick Start Card
# بطاقة البدء السريع للعرض التجريبي

---

## Login | تسجيل الدخول

| | |
|---|---|
| **URL** | **https://rs.fratelanza.com/login** (Real Estate platform) |
| **Not this** | `hub.fratelanza.com` is a different product (Fratelanza Hub) |
| **Username** | `demo_admin` (or `admin@demo.fratelanza.com`) |
| **Password** | `Demo123456` |

If `rs.fratelanza.com` opens Fratelanza Hub, use the direct link until DNS/nginx is fixed:  
**http://187.124.15.14:9000/login** — then on the VPS run `bash scripts/fix-rs-domain.sh`.

## RS control (Super Admin) | لوحة التحكم

| | |
|---|---|
| **URL** | **https://rs-control.fratelanza.com/super-admin** (or `/super-admin` on rs.fratelanza.com) |
| **Email** | `admin@fratelanza.com` |
| **Password** | Set on VPS — see `/opt/fratelanza/LOGIN_PASSWORD.txt` |

Same fix script also repairs `rs-control.fratelanza.com` if it opens Hub.

## Screenshots download | تحميل لقطات الشاشة

**ZIP (26 PNG + bilingual guides):**  
https://github.com/Refaat1942/Fratelanza-RS/raw/main/docs/fratelanza-demo-screenshots.zip

Guides: [EN](./DEMO-SCREENSHOTS-GUIDE.md) · [AR](./DEMO-SCREENSHOTS-GUIDE-AR.md)

---

## First step | الخطوة الأولى

**Dashboard → Load Demo Data**  
**لوحة التحكم → تحميل بيانات تجريبية**

---

## 5-minute tour | جولة 5 دقائق

```
Leads → Projects (click green unit) → Reservations (Approve ✓)
  → Contracts (Convert) → Collections (Record Payment)
```

| # | EN | AR | Action |
|---|----|----|--------|
| 1 | Leads | عملاء محتملون | Add lead / move kanban stage |
| 2 | Projects | مشاريع | Units Board → click available unit |
| 3 | Reservations | حجوزات | Approve → Convert to contract |
| 4 | Contracts | عقود | View linked customer & unit |
| 5 | Collections | تحصيل | Record payment on installment |

---

## Every list table | كل جدول

| Button | زر |
|--------|-----|
| **+ Add** | **+ إضافة** |
| **Edit** | **تعديل** |
| **Delete** | **حذف** |
| **Export Excel** | **تصدير Excel** |

---

## Full manuals | الأدلة الكاملة

- English: [DEMO-USER-MANUAL.md](./DEMO-USER-MANUAL.md)
- Arabic: [DEMO-USER-MANUAL-AR.md](./DEMO-USER-MANUAL-AR.md)

---

*Fratelanza Real Estate Platform — Demo*
