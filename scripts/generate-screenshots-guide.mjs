/**
 * Build bilingual markdown guides from screenshot manifest.
 */
import { readFile, writeFile } from 'fs/promises'
import { join } from 'path'

const DIR = process.env.SCREENSHOTS_DIR || join(process.cwd(), 'docs', 'demo-screenshots')
const manifest = JSON.parse(await readFile(join(DIR, 'manifest.json'), 'utf8'))

function section(shot, index) {
  const n = String(index + 1).padStart(2, '0')
  const enBullets = shot.features_en.map((f) => `- ${f}`).join('\n')
  const arBullets = shot.features_ar.map((f) => `- ${f}`).join('\n')
  return `
## ${n}. ${shot.title_en} / ${shot.title_ar}

![${shot.title_en}](./demo-screenshots/${shot.file})

| | |
|---|---|
| **Route** | \`${shot.path}\` |
| **Screenshot** | \`${shot.file}\` |

### English — Features & details

${enBullets}

### العربية — الميزات والتفاصيل

${arBullets}

---
`
}

const enHeader = `# Fratelanza Platform — Demo Screenshots Guide (English + Arabic)

**Audience:** Prospective customers evaluating the company demo (not Super Admin)  
**Login:** username \`demo_admin\` · password \`Demo123456\`  
**Total screens:** ${manifest.length}

Each screenshot includes a **bilingual overlay** (English left, Arabic right) describing every feature visible on that page.

> Arabic-only index: [DEMO-SCREENSHOTS-GUIDE-AR.md](./DEMO-SCREENSHOTS-GUIDE-AR.md)

---

## Quick start

1. Open the demo URL and log in with \`demo_admin\`
2. Click **Load Demo Data** on the Dashboard if tables are empty
3. Use the sidebar to open each module below
4. Match each screenshot to your live session

---

`

const arHeader = `# منصة فراتيلانزا — دليل لقطات الشاشة التجريبية (عربي + إنجليزي)

**الجمهور:** العملاء المحتملون لتقييم النسخة التجريبية (بدون المشرف العام)  
**تسجيل الدخول:** اسم المستخدم \`demo_admin\` · كلمة المرور \`Demo123456\`  
**عدد الشاشات:** ${manifest.length}

كل لقطة تحتوي على **شرح ثنائي اللغة** (إنجليزي يسار، عربي يمين) يوضح كل ميزة في الصفحة.

> English index: [DEMO-SCREENSHOTS-GUIDE.md](./DEMO-SCREENSHOTS-GUIDE.md)

---

## البدء السريع

1. افتح رابط العرض وسجّل الدخول بـ \`demo_admin\`
2. اضغط **تحميل بيانات تجريبية** من لوحة التحكم إذا كانت الجداول فارغة
3. استخدم القائمة الجانبية لفتح كل وحدة أدناه
4. قارن كل لقطة مع جلستك المباشرة

---

`

await writeFile(join(process.cwd(), 'docs', 'DEMO-SCREENSHOTS-GUIDE.md'), enHeader + manifest.map(section).join('\n'))
await writeFile(join(process.cwd(), 'docs', 'DEMO-SCREENSHOTS-GUIDE-AR.md'), arHeader + manifest.map(section).join('\n'))
console.log('Wrote DEMO-SCREENSHOTS-GUIDE.md and DEMO-SCREENSHOTS-GUIDE-AR.md')
