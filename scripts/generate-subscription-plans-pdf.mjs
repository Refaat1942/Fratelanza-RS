/**
 * Generates customer-facing subscription plans PDF (Arabic + English).
 * Usage: node scripts/generate-subscription-plans-pdf.mjs
 * Optional: DEMO_URL + SUPER_ADMIN credentials to pull live plan data from API.
 */
import { chromium } from 'playwright'
import { mkdir, writeFile, readFile } from 'fs/promises'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const OUT_DIR = process.env.ARTIFACTS_DIR || '/opt/cursor/artifacts'
const MARKETING_DIR = join(__dirname, '..', 'docs', 'marketing')
const PDF_PATH = join(OUT_DIR, 'fratelanza-subscription-plans.pdf')
const PDF_COPY = join(MARKETING_DIR, 'fratelanza-subscription-plans.pdf')

const BASE_URL = process.env.DEMO_URL || 'https://rs.fratelanza.com'
const API_BASE = `${BASE_URL}/api/v1`

const MODULE_LABELS = {
  dashboard: { en: 'Dashboard & KPIs', ar: 'لوحة التحكم والمؤشرات' },
  customers: { en: 'Customers CRM', ar: 'إدارة العملاء' },
  leads: { en: 'Leads & Sales Pipeline', ar: 'العملاء المحتملون ومسار المبيعات' },
  follow_ups: { en: 'Follow-ups & Calls', ar: 'المتابعات والمكالمات' },
  projects: { en: 'Projects & Units', ar: 'المشاريع والوحدات' },
  reservations: { en: 'Reservations', ar: 'الحجوزات' },
  contracts: { en: 'Contracts', ar: 'العقود' },
  collections: { en: 'Collections & Installments', ar: 'التحصيل والأقساط' },
  brokers: { en: 'Brokers Portal', ar: 'بوابة الوسطاء' },
  finance: { en: 'Finance & Accounting', ar: 'المالية والمحاسبة' },
  hr: { en: 'HR & Payroll', ar: 'الموارد البشرية والرواتب' },
  construction: { en: 'Construction Management', ar: 'إدارة المقاولات' },
  procurement: { en: 'Procurement', ar: 'المشتريات' },
  warehouse: { en: 'Warehouse & Inventory', ar: 'المستودع والمخزون' },
  property: { en: 'Property Management', ar: 'إدارة الممتلكات' },
  customer_service: { en: 'Customer Service Tickets', ar: 'خدمة العملاء والتذاكر' },
  users: { en: 'Team Users & Roles', ar: 'مستخدمي الفريق والصلاحيات' },
  reports: { en: 'Reports & Excel Export', ar: 'التقارير وتصدير Excel' },
  branding: { en: 'Company Branding', ar: 'الهوية البصرية للشركة' },
  ai_assistant: { en: 'AI Assistant', ar: 'المساعد الذكي' },
}

const FALLBACK_PLANS = [
  {
    code: 'basic',
    name_en: 'Basic',
    name_ar: 'أساسي',
    price_monthly: 999,
    price_yearly: 9999,
    max_users: 10,
    max_projects: 3,
    max_storage_mb: 2048,
    enabled_modules: [
      'dashboard', 'customers', 'leads', 'follow_ups', 'projects',
      'reservations', 'contracts', 'collections', 'users', 'branding', 'reports',
    ],
  },
  {
    code: 'professional',
    name_en: 'Professional',
    name_ar: 'احترافي',
    price_monthly: 2499,
    price_yearly: 24999,
    max_users: 50,
    max_projects: 15,
    max_storage_mb: 10240,
    enabled_modules: [
      'dashboard', 'customers', 'leads', 'follow_ups', 'projects',
      'reservations', 'contracts', 'collections', 'brokers', 'finance', 'hr',
      'users', 'reports', 'branding', 'customer_service',
    ],
  },
  {
    code: 'enterprise',
    name_en: 'Enterprise',
    name_ar: 'مؤسسي',
    price_monthly: 4999,
    price_yearly: 49999,
    max_users: 500,
    max_projects: 100,
    max_storage_mb: 51200,
    enabled_modules: Object.keys(MODULE_LABELS),
  },
]

async function fetchLivePlans() {
  const email = process.env.SUPER_ADMIN_EMAIL || 'admin@fratelanza.com'
  const password = process.env.SUPER_ADMIN_PASSWORD || 'SuperAdmin2026'
  try {
    const loginRes = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!loginRes.ok) return FALLBACK_PLANS
    const tokens = await loginRes.json()
    const plansRes = await fetch(`${API_BASE}/super-admin/subscription-plans`, {
      headers: { Authorization: `Bearer ${tokens.access_token}` },
    })
    if (!plansRes.ok) return FALLBACK_PLANS
    const plans = await plansRes.json()
    if (!Array.isArray(plans) || plans.length === 0) return FALLBACK_PLANS
    console.log('✓ Loaded live plans from API')
    return plans
  } catch {
    console.log('Using default plan catalog (API unavailable)')
    return FALLBACK_PLANS
  }
}

function formatEgp(n) {
  return new Intl.NumberFormat('en-EG', { style: 'currency', currency: 'EGP', maximumFractionDigits: 0 }).format(Number(n))
}

function formatStorage(mb) {
  if (mb >= 1024) return `${(mb / 1024).toFixed(0)} GB`
  return `${mb} MB`
}

function featureRows(allKeys, enabled) {
  const set = new Set(enabled)
  return allKeys.map((key) => {
    const labels = MODULE_LABELS[key] || { en: key, ar: key }
    const on = set.has(key)
    return `<tr class="${on ? 'included' : 'excluded'}">
      <td>${on ? '✓' : '—'}</td>
      <td>${labels.en}</td>
      <td dir="rtl">${labels.ar}</td>
    </tr>`
  }).join('')
}

function buildHtml(plans, generatedAt) {
  const allKeys = Object.keys(MODULE_LABELS)
  const planCards = plans.map((p, i) => {
    const accent = ['#0159a1', '#7c3aed', '#059669'][i] || '#0159a1'
    const modules = p.enabled_modules || []
    return `
    <div class="plan-card" style="--accent:${accent}">
      <div class="plan-badge">${p.code.toUpperCase()}</div>
      <h2>${p.name_en} <span dir="rtl">/ ${p.name_ar}</span></h2>
      <div class="price-row">
        <div><span class="price">${formatEgp(p.price_monthly)}</span><span class="period">/ month</span></div>
        <div class="yearly">or ${formatEgp(p.price_yearly)} / year <em>(save 2 months)</em></div>
      </div>
      <ul class="limits">
        <li><strong>${p.max_users}</strong> users / <span dir="rtl">مستخدم</span></li>
        <li><strong>${p.max_projects}</strong> projects / <span dir="rtl">مشروع</span></li>
        <li><strong>${formatStorage(p.max_storage_mb)}</strong> storage / <span dir="rtl">تخزين</span></li>
      </ul>
      <p class="modules-count">${modules.length} modules included / <span dir="rtl">${modules.length} وحدة مفعّلة</span></p>
    </div>`
  }).join('')

  const comparisonRows = allKeys.map((key) => {
    const labels = MODULE_LABELS[key]
    const cells = plans.map((p) => {
      const on = (p.enabled_modules || []).includes(key)
      return `<td class="${on ? 'yes' : 'no'}">${on ? '✓' : ''}</td>`
    }).join('')
    return `<tr>
      <td>${labels.en}<br><span dir="rtl" class="ar-sm">${labels.ar}</span></td>
      ${cells}
    </tr>`
  }).join('')

  const detailSections = plans.map((p, i) => {
    const accent = ['#0159a1', '#7c3aed', '#059669'][i] || '#0159a1'
    return `
    <section class="plan-detail page-break" style="--accent:${accent}">
      <h2>${p.name_en} Plan — <span dir="rtl">باقة ${p.name_ar}</span></h2>
      <table class="features-table">
        <thead><tr><th></th><th>Feature</th><th dir="rtl">الميزة</th></tr></thead>
        <tbody>${featureRows(allKeys, p.enabled_modules || [])}</tbody>
      </table>
    </section>`
  }).join('')

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>FRATELANZA Subscription Plans</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&family=Inter:wght@400;600;700&display=swap" rel="stylesheet" />
  <style>
    @page { size: A4; margin: 14mm 12mm; }
    * { box-sizing: border-box; }
    body {
      font-family: 'Inter', 'Cairo', 'Segoe UI', Tahoma, Arial, sans-serif;
      color: #0f172a; line-height: 1.45; font-size: 10.5pt; margin: 0;
    }
    .cover {
      min-height: 260mm; display: flex; flex-direction: column; justify-content: center;
      background: linear-gradient(135deg, #072849 0%, #0159a1 45%, #0ea5e9 100%);
      color: white; padding: 48px; border-radius: 12px; margin-bottom: 24px;
    }
    .cover h1 { font-size: 36pt; margin: 0 0 8px; letter-spacing: 1px; }
    .cover .subtitle { font-size: 14pt; opacity: 0.9; margin-bottom: 32px; }
    .cover .tagline { font-size: 11pt; opacity: 0.85; max-width: 480px; }
    .gold { color: #d4a853; }
    .meta { margin-top: 48px; font-size: 9pt; opacity: 0.75; }
    h2.section-title {
      font-size: 16pt; color: #0159a1; border-bottom: 3px solid #d4a853;
      padding-bottom: 6px; margin: 28px 0 16px;
    }
    .intro { background: #f0f7ff; border-radius: 10px; padding: 16px 20px; margin-bottom: 20px; }
    .plans-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px; }
    .plan-card {
      border: 2px solid var(--accent); border-radius: 12px; padding: 16px;
      background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
    }
    .plan-badge {
      display: inline-block; background: var(--accent); color: white;
      font-size: 8pt; font-weight: 700; padding: 3px 10px; border-radius: 999px; margin-bottom: 8px;
    }
    .plan-card h2 { font-size: 13pt; margin: 0 0 10px; color: var(--accent); }
    .price { font-size: 18pt; font-weight: 800; color: #0f172a; }
    .period { font-size: 9pt; color: #64748b; }
    .yearly { font-size: 9pt; color: #475569; margin-top: 4px; }
    .limits { list-style: none; padding: 0; margin: 12px 0 0; font-size: 9pt; }
    .limits li { padding: 4px 0; border-top: 1px solid #e2e8f0; }
    .modules-count { font-size: 8.5pt; color: #64748b; margin: 10px 0 0; }
    table.compare { width: 100%; border-collapse: collapse; font-size: 8.5pt; }
    table.compare th, table.compare td { border: 1px solid #e2e8f0; padding: 6px 8px; text-align: center; }
    table.compare th { background: #0159a1; color: white; }
    table.compare td:first-child { text-align: left; font-weight: 500; }
    table.compare .yes { background: #ecfdf5; color: #059669; font-weight: 700; }
    table.compare .no { background: #f8fafc; color: #cbd5e1; }
    .ar-sm { font-size: 8pt; color: #64748b; }
    [dir="rtl"], .ar-sm, .subtitle { font-family: 'Cairo', 'Noto Naskh Arabic', Arial, sans-serif; }
    .payment-box {
      display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 16px 0;
    }
    .payment-box div {
      background: #fffbeb; border: 1px solid #fcd34d; border-radius: 10px; padding: 14px;
    }
    .contact-box {
      background: linear-gradient(135deg, #072849, #0159a1); color: white;
      border-radius: 12px; padding: 20px 24px; margin-top: 24px;
    }
    .contact-box a { color: #d4a853; }
    .plan-detail h2 { color: var(--accent); border-bottom: 2px solid var(--accent); padding-bottom: 6px; }
    table.features-table { width: 100%; border-collapse: collapse; font-size: 9pt; }
    table.features-table th { background: var(--accent); color: white; padding: 8px; text-align: left; }
    table.features-table td { border-bottom: 1px solid #e2e8f0; padding: 5px 8px; }
    tr.included td { background: #f0fdf4; }
    tr.excluded td { background: #f8fafc; color: #94a3b8; }
    tr.included td:first-child { color: #059669; font-weight: 700; }
    .page-break { page-break-before: always; }
    .footer-note { font-size: 8pt; color: #64748b; text-align: center; margin-top: 32px; }
  </style>
</head>
<body>
  <div class="cover">
    <div class="gold" style="font-size:11pt;font-weight:700;">FRATELANZA REAL ESTATE PLATFORM</div>
    <h1>Subscription Plans</h1>
    <div class="subtitle" dir="rtl">باقات الاشتراك — منصة فراتيلانزا العقارية</div>
    <p class="tagline">
      Complete cloud ERP & CRM for real estate developers in Egypt.
      Arabic RTL + English — sales, contracts, collections, finance, HR & more.
    </p>
    <p class="tagline" dir="rtl" style="margin-top:12px;">
      منصة سحابية متكاملة لشركات التطوير العقاري في مصر — عربي وإنجليزي.
    </p>
    <div class="meta">Generated: ${generatedAt} · rs.fratelanza.com</div>
  </div>

  <h2 class="section-title">Overview / نظرة عامة</h2>
  <div class="intro">
    <p><strong>Choose the plan that fits your company size.</strong> All plans include secure cloud hosting,
    automatic updates, data isolation per company, and bilingual Arabic/English interface.</p>
    <p dir="rtl"><strong>اختر الباقة المناسبة لحجم شركتك.</strong> جميع الباقات تشمل استضافة سحابية آمنة،
    تحديثات تلقائية، عزل بيانات لكل شركة، وواجهة ثنائية اللغة عربي/إنجليزي.</p>
  </div>

  <h2 class="section-title">Plans & Pricing / الباقات والأسعار</h2>
  <div class="plans-grid">${planCards}</div>

  <h2 class="section-title">Feature Comparison / مقارنة الميزات</h2>
  <table class="compare">
    <thead>
      <tr>
        <th>Feature / الميزة</th>
        ${plans.map((p) => `<th>${p.name_en}<br><span dir="rtl">${p.name_ar}</span></th>`).join('')}
      </tr>
    </thead>
    <tbody>${comparisonRows}</tbody>
  </table>

  <h2 class="section-title">Payment Terms / شروط الدفع</h2>
  <div class="payment-box">
    <div>
      <strong>Billing cycles</strong> — Monthly or yearly (yearly = 2 months free).<br>
      <span dir="rtl"><strong>دورات الفوترة</strong> — شهري أو سنوي (التوفير شهرين مع السنوي).</span>
    </div>
    <div>
      <strong>Payment terms</strong> — Net 30 days from invoice date. Bank transfer or agreed method.<br>
      <span dir="rtl"><strong>شروط السداد</strong> — صافي 30 يوماً من تاريخ الفاتورة. تحويل بنكي أو طريقة متفق عليها.</span>
    </div>
    <div>
      <strong>Trial</strong> — 14-day trial available for new companies.<br>
      <span dir="rtl"><strong>تجربة</strong> — فترة تجريبية 14 يوماً للشركات الجديدة.</span>
    </div>
    <div>
      <strong>Reminders</strong> — Payment reminders sent before and after due date.<br>
      <span dir="rtl"><strong>تذكيرات</strong> — إرسال تذكيرات قبل وبعد تاريخ الاستحقاق.</span>
    </div>
  </div>

  <div class="contact-box">
    <h3 style="margin:0 0 12px;">Customer Service / خدمة العملاء</h3>
    <p style="margin:0 0 8px;">
      <strong>Email:</strong> <a href="mailto:support@fratelanza.com">support@fratelanza.com</a> ·
      <strong>Web:</strong> <a href="https://rs.fratelanza.com">rs.fratelanza.com</a>
    </p>
    <p dir="rtl" style="margin:0;font-size:10pt;">
      للاشتراك أو ترقية الباقة، تواصل مع فريق خدمة العملاء. يمكن تخصيص الباقة المؤسسية حسب احتياجاتكم.
    </p>
    <p style="margin:12px 0 0;font-size:9pt;opacity:0.85;">
      To subscribe or upgrade, contact our customer service team. Enterprise plans can be customized.
    </p>
  </div>

  ${detailSections}

  <p class="footer-note">
    © FRATELANZA Real Estate Platform · Prices in EGP · Subject to change · Document generated ${generatedAt}
  </p>
</body>
</html>`
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true })
  await mkdir(MARKETING_DIR, { recursive: true })

  const plans = await fetchLivePlans()
  const generatedAt = new Date().toLocaleDateString('en-GB', { year: 'numeric', month: 'long', day: 'numeric' })
  const html = buildHtml(plans, generatedAt)
  const htmlPath = join(OUT_DIR, 'subscription-plans-brochure.html')
  await writeFile(htmlPath, html)

  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage()
  await page.setContent(html, { waitUntil: 'networkidle' })
  await page.evaluate(() => document.fonts.ready)
  await page.pdf({
    path: PDF_PATH,
    format: 'A4',
    printBackground: true,
    margin: { top: '10mm', bottom: '10mm', left: '10mm', right: '10mm' },
  })
  await browser.close()

  await writeFile(PDF_COPY, await readFile(PDF_PATH))
  console.log(`PDF: ${PDF_PATH}`)
  console.log(`Copy: ${PDF_COPY}`)
  console.log(`HTML preview: ${htmlPath}`)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
