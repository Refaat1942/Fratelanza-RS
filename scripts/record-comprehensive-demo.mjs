/**
 * Comprehensive platform demo — Super Admin + all company modules (Arabic UI).
 */
import { chromium } from 'playwright'
import { mkdir, writeFile } from 'fs/promises'
import { join } from 'path'

const BASE_URL = process.env.DEMO_URL || 'https://rs.fratelanza.com'
const API_BASE = `${BASE_URL}/api/v1`
const OUT_DIR = process.env.ARTIFACTS_DIR || '/opt/cursor/artifacts'
const VIDEO_DIR = join(OUT_DIR, 'comprehensive-demo-raw')
const LOCALE = process.env.DEMO_LOCALE || 'ar'

const SUPER_ADMIN = { email: 'admin@fratelanza.com', password: 'SuperAdmin2026' }
const DEMO = { email: 'admin@demo.fratelanza.com', password: 'Demo123456' }

const ALL_MODULES = [
  'dashboard', 'customers', 'leads', 'follow_ups', 'projects', 'reservations',
  'contracts', 'collections', 'brokers', 'finance', 'hr', 'construction',
  'procurement', 'warehouse', 'property', 'customer_service', 'users',
  'reports', 'branding', 'ai_assistant',
]

const SUPER_ADMIN_PAGES = [
  ['/super-admin', 'لوحة تحكم مدير المنصة — إحصائيات شاملة'],
  ['/super-admin/companies', 'إدارة الشركات — الاشتراكات وشروط الدفع والتذكيرات'],
  ['/super-admin/users', 'إدارة المستخدمين — الشركات والأدوار وإعادة كلمة المرور'],
  ['/super-admin/subscriptions', 'باقات الاشتراك — تحديد الميزات لكل باقة'],
  ['/super-admin/settings', 'إعدادات المنصة — النسخ الاحتياطي والإحصائيات'],
  ['/super-admin/audit-logs', 'سجل التدقيق — تتبع كل العمليات'],
  ['/super-admin/reports', 'تقارير المنصة — تحليلات على مستوى النظام'],
]

const COMPANY_SECTIONS = [
  {
    title: 'لوحة التحكم وإدارة العملاء',
    pages: [
      ['/dashboard', 'لوحة التحكم — مؤشرات الأداء والمبيعات والتحصيل'],
      ['/customers', 'العملاء — CRM واستيراد ذكي من Excel'],
      ['/leads', 'العملاء المحتملون — مسار مبيعات Kanban'],
      ['/follow-ups', 'المتابعات — قائمة مكالمات وجدولة'],
    ],
  },
  {
    title: 'المبيعات والعقارات',
    pages: [
      ['/projects', 'المشاريع — مباني وطوابق ووحدات'],
      ['/reservations', 'الحجوزات — حجز الوحدات'],
      ['/contracts', 'العقود — اتفاقيات البيع'],
      ['/collections', 'التحصيل — أقساط ومدفوعات'],
      ['/brokers', 'الوسطاء — إدارة الوسطاء العقاريين'],
    ],
  },
  {
    title: 'العمليات والمقاولات',
    pages: [
      ['/construction', 'المقاولات — مراحل ومهام المشاريع'],
      ['/procurement', 'المشتريات — طلبات الشراء'],
      ['/warehouse', 'المستودع — المخزون والمواد'],
      ['/property', 'إدارة الممتلكات — صيانة وتشغيل'],
    ],
  },
  {
    title: 'المالية والموارد البشرية',
    pages: [
      ['/finance', 'المالية — دليل حسابات وقيود يومية'],
      ['/hr', 'الموارد البشرية — موظفون ورواتب'],
    ],
  },
  {
    title: 'الدعم والتحليلات والإدارة',
    pages: [
      ['/customer-service', 'خدمة العملاء — تذاكر الدعم'],
      ['/reports', 'التقارير — جداول قابلة للتصدير'],
      ['/ai-assistant', 'المساعد الذكي — تحليلات وتوصيات AI'],
      ['/users', 'مستخدمي الفريق — صلاحيات الفريق'],
      ['/branding', 'الهوية البصرية — شعار واسم الشركة'],
    ],
  },
]

async function pause(page, ms = 2400) {
  await page.waitForTimeout(ms)
}

async function setLocale(page) {
  await page.addInitScript((lang) => {
    localStorage.setItem('language', lang)
    document.documentElement.lang = lang
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'
  }, LOCALE)
}

async function showOverlay(page, text, { section = false } = {}) {
  const dir = LOCALE === 'ar' ? 'rtl' : 'ltr'
  await page.evaluate(({ text, section, dir }) => {
    document.getElementById('demo-overlay')?.remove()
    const el = document.createElement('div')
    el.id = 'demo-overlay'
    el.textContent = text
    Object.assign(el.style, {
      position: 'fixed',
      ...(section
        ? { inset: '0', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '32px' }
        : { bottom: '20px', left: '50%', transform: 'translateX(-50%)', fontSize: '17px', maxWidth: '92%' }),
      zIndex: '99999',
      background: section
        ? 'linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0ea5e9 100%)'
        : 'linear-gradient(135deg, #0f172a 0%, #1e40af 100%)',
      color: '#fff',
      padding: section ? '48px' : '12px 24px',
      borderRadius: section ? '0' : '12px',
      fontWeight: section ? '700' : '600',
      fontFamily: 'Tahoma, Arial, sans-serif',
      boxShadow: section ? 'none' : '0 8px 32px rgba(0,0,0,0.35)',
      textAlign: 'center',
      direction: dir,
      lineHeight: '1.4',
      whiteSpace: 'pre-line',
    })
    document.body.appendChild(el)
  }, { text, section, dir })
}

async function clearOverlay(page) {
  await page.evaluate(() => document.getElementById('demo-overlay')?.remove())
}

async function login(page, creds) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' })
  await pause(page, 800)
  await page.fill('input[type="email"]', creds.email)
  await page.fill('input[type="password"]', creds.password)
  await page.click('button[type="submit"]')
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 30000 })
  await pause(page, 1500)
}

async function logout(page) {
  const btn = page.getByRole('button', { name: /logout|تسجيل الخروج/i })
  if (await btn.count()) {
    await btn.first().click()
    await page.waitForURL('**/login**', { timeout: 15000 }).catch(() => {})
    await pause(page, 1000)
  }
}

async function getAuthToken(page) {
  return page.evaluate(() => {
    try {
      const raw = localStorage.getItem('fratelanza-auth')
      return raw ? JSON.parse(raw).state?.accessToken : null
    } catch {
      return null
    }
  })
}

async function enableAllDemoModules(page) {
  const token = await getAuthToken(page)
  if (!token) return
  const companiesRes = await page.request.get(`${API_BASE}/super-admin/companies?page_size=100`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  const companies = await companiesRes.json()
  const demo = companies.items?.find((c) => c.code === 'DEMO')
  if (!demo) return
  await page.request.put(`${API_BASE}/modules/company/${demo.id}`, {
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    data: { enabled_modules: ALL_MODULES },
  })
  console.log(`✓ Enabled all ${ALL_MODULES.length} modules for DEMO company`)
}

async function visit(page, path, caption) {
  console.log(`→ ${caption}`)
  await page.goto(`${BASE_URL}${path}`, { waitUntil: 'networkidle' })
  await showOverlay(page, caption)
  await pause(page, 2600)
}

async function visitSettingsTabs(page) {
  await visit(page, '/super-admin/settings', 'إعدادات المنصة')
  for (const tabLabel of [/platform|إعدادات المنصة/i, /backup|نسخ/i, /stats|إحصائيات/i]) {
    const tab = page.getByRole('button', { name: tabLabel })
    if (await tab.count()) {
      await tab.first().click()
      await pause(page, 2000)
    }
  }
  await clearOverlay(page)
}

async function showSection(page, title) {
  console.log(`══ ${title} ══`)
  await page.goto(`${BASE_URL}/dashboard`, { waitUntil: 'networkidle' }).catch(() => {})
  await showOverlay(page, title, { section: true })
  await pause(page, 2200)
  await clearOverlay(page)
}

async function main() {
  await mkdir(VIDEO_DIR, { recursive: true })
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: VIDEO_DIR, size: { width: 1280, height: 720 } },
    locale: LOCALE === 'ar' ? 'ar-EG' : 'en-US',
  })
  const page = await context.newPage()
  await setLocale(page)

  try {
    // Login screen
    await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' })
    await showOverlay(page, 'فراتيلانزا — منصة العقارات المتكاملة\nERP • CRM • مالية • مقاولات • عربي كامل', { section: true })
    await pause(page, 2500)
    await clearOverlay(page)

    // ── Super Admin ──
    await showSection(page, 'الجزء ١ — إدارة المنصة (Super Admin)')
    await login(page, SUPER_ADMIN)
    for (const [path, caption] of SUPER_ADMIN_PAGES) {
      if (path.includes('settings')) {
        await visitSettingsTabs(page)
      } else {
        await visit(page, path, caption)
      }
    }
    await enableAllDemoModules(page)
    await logout(page)

    // ── Company features ──
    await showSection(page, 'الجزء ٢ — ميزات الشركة (جميع الوحدات)')
    await login(page, DEMO)

    for (const section of COMPANY_SECTIONS) {
      await showSection(page, section.title)
      for (const [path, caption] of section.pages) {
        await visit(page, path, caption)
      }
    }

    await showOverlay(page, 'شكراً — FRATELANZA Real Estate Platform\nمنصة فراتيلانزا العقارية', { section: true })
    await pause(page, 3000)
  } catch (err) {
    console.error('Recording error:', err)
    await writeFile(join(OUT_DIR, 'comprehensive-demo-error.txt'), String(err.stack || err))
  } finally {
    await page.close()
    await context.close()
    await browser.close()
  }
  console.log(`Raw video: ${VIDEO_DIR}`)
}

main()
