/**
 * Customer-facing detailed demo — all company features, no Super Admin UI.
 * Starts with customer intro, logs in as demo company, walks every module in depth.
 */
import { chromium } from 'playwright'
import { mkdir, writeFile } from 'fs/promises'
import { join } from 'path'

const BASE_URL = process.env.DEMO_URL || 'https://rs.fratelanza.com'
const API_BASE = `${BASE_URL}/api/v1`
const OUT_DIR = process.env.ARTIFACTS_DIR || '/opt/cursor/artifacts'
const VIDEO_DIR = join(OUT_DIR, 'customer-demo-raw')
const LOCALE = process.env.DEMO_LOCALE || 'ar'

const SUPER_ADMIN = { email: 'admin@fratelanza.com', password: 'SuperAdmin2026' }
const DEMO = { email: 'admin@demo.fratelanza.com', password: 'Demo123456' }

const ALL_MODULES = [
  'dashboard', 'customers', 'leads', 'follow_ups', 'projects', 'reservations',
  'contracts', 'collections', 'brokers', 'finance', 'hr', 'construction',
  'procurement', 'warehouse', 'property', 'customer_service', 'users',
  'reports', 'branding', 'ai_assistant',
]

/** Detailed customer tour — path, caption, optional interactions */
const TOUR = [
  {
    section: 'مرحباً بكم في فراتيلانزا\nمنصة العقارات المتكاملة لشركتكم',
    pages: [],
    introOnly: true,
  },
  {
    section: '١ — لوحة التحكم والمؤشرات',
    pages: [
      { path: '/dashboard', caption: 'لوحة التحكم — مؤشرات المبيعات والتحصيل والوحدات المتاحة', scroll: 500, dwell: 4000 },
    ],
  },
  {
    section: '٢ — إدارة العملاء CRM',
    pages: [
      { path: '/customers', caption: 'قاعدة بيانات العملاء — بحث، إضافة، واستيراد ذكي من Excel', scroll: 350, dwell: 3800 },
      { path: '/leads', caption: 'مسار المبيعات Kanban — تتبع العملاء المحتملين حتى الإغلاق', actions: ['leads-kanban', 'leads-list'], dwell: 4200 },
      { path: '/follow-ups', caption: 'مركز المكالمات — قائمة الانتظار، الجدولة، وتسجيل نتائج المكالمات', actions: ['followups-queue', 'followups-history'], scroll: 300, dwell: 4200 },
    ],
  },
  {
    section: '٣ — المشاريع العقارية والمبيعات',
    pages: [
      { path: '/projects', caption: 'المشاريع — لوحة الوحدات: مباني، طوابق، حالة كل وحدة', actions: ['projects-board', 'projects-list'], dwell: 4000 },
      { path: '/reservations', caption: 'الحجوزات — حجز الوحدات وتواريخ الانتهاء', scroll: 300, dwell: 3200 },
      { path: '/contracts', caption: 'العقود — اتفاقيات البيع وقيمة الصفقات', scroll: 300, dwell: 3200 },
      { path: '/collections', caption: 'التحصيل — جداول الأقساط والمدفوعات والمتأخرات', scroll: 350, dwell: 3500 },
      { path: '/brokers', caption: 'الوسطاء العقاريون — إدارة الشركاء والعمولات', scroll: 300, dwell: 3000 },
    ],
  },
  {
    section: '٤ — المقاولات والعمليات',
    pages: [
      { path: '/construction', caption: 'إدارة المقاولات — مراحل المشروع والمهام', scroll: 300, dwell: 3000 },
      { path: '/procurement', caption: 'المشتريات — طلبات الشراء والموردين', scroll: 300, dwell: 3000 },
      { path: '/warehouse', caption: 'المستودع — المخزون والمواد', scroll: 300, dwell: 3000 },
      { path: '/property', caption: 'إدارة الممتلكات — صيانة وتشغيل العقارات', scroll: 300, dwell: 3000 },
    ],
  },
  {
    section: '٥ — المالية والموارد البشرية',
    pages: [
      { path: '/finance', caption: 'المالية — دليل الحسابات والقيود اليومية والتقارير المالية', scroll: 400, dwell: 3800 },
      { path: '/hr', caption: 'الموارد البشرية — الموظفون، الرواتب، ومسيرات الصرف', scroll: 350, dwell: 3500 },
    ],
  },
  {
    section: '٦ — التقارير والذكاء الاصطناعي',
    pages: [
      { path: '/reports', caption: 'مركز التقارير — جداول تفاعلية وتصدير Excel', scroll: 350, dwell: 3500 },
      { path: '/ai-assistant', caption: 'المساعد الذكي — اسأل عن المبيعات والتحصيلات والأداء', actions: ['ai-demo'], dwell: 4500 },
    ],
  },
  {
    section: '٧ — إدارة الفريق والهوية',
    pages: [
      { path: '/customer-service', caption: 'خدمة العملاء — تذاكر الدعم ومتابعة الطلبات', scroll: 300, dwell: 3000 },
      { path: '/users', caption: 'مستخدمي الفريق — الأدوار والصلاحيات', scroll: 300, dwell: 3000 },
      { path: '/branding', caption: 'الهوية البصرية — شعار واسم شركتكم على المنصة', dwell: 3500 },
    ],
  },
]

async function pause(page, ms) {
  await page.waitForTimeout(ms)
}

async function setLocale(page) {
  await page.addInitScript((lang) => {
    localStorage.setItem('language', lang)
    document.documentElement.lang = lang
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'
  }, LOCALE)
}

async function showOverlay(page, text, { section = false, subtitle = '' } = {}) {
  const dir = LOCALE === 'ar' ? 'rtl' : 'ltr'
  await page.evaluate(({ text, section, subtitle, dir }) => {
    document.getElementById('demo-overlay')?.remove()
    const wrap = document.createElement('div')
    wrap.id = 'demo-overlay'
    Object.assign(wrap.style, {
      position: 'fixed',
      inset: section ? '0' : 'auto',
      bottom: section ? 'auto' : '20px',
      left: section ? '0' : '50%',
      right: section ? '0' : 'auto',
      transform: section ? 'none' : 'translateX(-50%)',
      zIndex: '99999',
      display: section ? 'flex' : 'block',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: section
        ? 'linear-gradient(135deg, #072849 0%, #0159a1 40%, #0ea5e9 100%)'
        : 'linear-gradient(135deg, #0f172a 0%, #1e40af 100%)',
      color: '#fff',
      padding: section ? '48px' : '14px 28px',
      fontWeight: section ? '700' : '600',
      fontFamily: 'Tahoma, Arial, sans-serif',
      boxShadow: section ? 'none' : '0 8px 32px rgba(0,0,0,0.35)',
      textAlign: 'center',
      direction: dir,
      lineHeight: '1.5',
      maxWidth: section ? '100%' : '92%',
    })
    const title = document.createElement('div')
    title.textContent = text
    title.style.fontSize = section ? '34px' : '17px'
    title.style.whiteSpace = 'pre-line'
    wrap.appendChild(title)
    if (subtitle) {
      const sub = document.createElement('div')
      sub.textContent = subtitle
      sub.style.fontSize = section ? '16px' : '13px'
      sub.style.marginTop = '16px'
      sub.style.opacity = '0.9'
      sub.style.fontWeight = '400'
      wrap.appendChild(sub)
    }
    if (section) {
      const badge = document.createElement('div')
      badge.textContent = 'FRATELANZA · عرض للعملاء'
      badge.style.marginTop = '28px'
      badge.style.fontSize = '12px'
      badge.style.letterSpacing = '2px'
      badge.style.opacity = '0.75'
      wrap.appendChild(badge)
    }
    document.body.appendChild(wrap)
  }, { text, section, subtitle, dir })
}

async function clearOverlay(page) {
  await page.evaluate(() => document.getElementById('demo-overlay')?.remove())
}

async function scrollPage(page, amount = 400) {
  await page.evaluate((y) => window.scrollBy({ top: y, behavior: 'smooth' }), amount)
  await pause(page, 1200)
}

async function enableAllDemoModules() {
  try {
    const loginRes = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(SUPER_ADMIN),
    })
    if (!loginRes.ok) return
    const { access_token } = await loginRes.json()
    const companiesRes = await fetch(`${API_BASE}/super-admin/companies?page_size=100`, {
      headers: { Authorization: `Bearer ${access_token}` },
    })
    const companies = await companiesRes.json()
    const demo = companies.items?.find((c) => c.code === 'DEMO')
    if (!demo) return
    await fetch(`${API_BASE}/modules/company/${demo.id}`, {
      method: 'PUT',
      headers: { Authorization: `Bearer ${access_token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled_modules: ALL_MODULES }),
    })
    console.log(`✓ All ${ALL_MODULES.length} modules enabled for DEMO`)
  } catch (e) {
    console.warn('Module setup skipped:', e.message)
  }
}

async function runActions(page, actions = []) {
  for (const action of actions) {
    switch (action) {
      case 'leads-list': {
        const btn = page.getByRole('button', { name: /list|قائمة/i })
        if (await btn.count()) { await btn.first().click(); await pause(page, 2000) }
        break
      }
      case 'leads-kanban':
        break
      case 'followups-history': {
        const tab = page.getByRole('button', { name: /history|السجل|سجل/i })
        if (await tab.count()) { await tab.first().click(); await pause(page, 2200) }
        break
      }
      case 'followups-queue': {
        const tab = page.getByRole('button', { name: /queue|قائمة|انتظار/i })
        if (await tab.count()) { await tab.first().click(); await pause(page, 1500) }
        break
      }
      case 'projects-list': {
        const btn = page.getByRole('button', { name: /list|قائمة|projects_list/i })
        if (await btn.count()) { await btn.first().click(); await pause(page, 2000) }
        break
      }
      case 'projects-board':
        break
      case 'ai-demo': {
        const input = page.locator('input[type="text"], input:not([type])').last()
        if (await input.count()) {
          await input.fill('ما هي أهم مؤشرات المبيعات هذا الشهر؟')
          await pause(page, 600)
          await page.keyboard.press('Enter')
          await pause(page, 3000)
        }
        break
      }
    }
  }
}

async function visitPage(page, { path, caption, scroll = 0, dwell = 3200, actions = [] }) {
  console.log(`→ ${caption}`)
  await page.goto(`${BASE_URL}${path}`, { waitUntil: 'networkidle', timeout: 45000 })
  await pause(page, 1000)
  await showOverlay(page, caption)
  await pause(page, Math.min(dwell, 2200))
  await clearOverlay(page)
  await runActions(page, actions)
  if (scroll) await scrollPage(page, scroll)
  await pause(page, Math.max(dwell - 2200, 1500))
}

async function showSection(page, title) {
  console.log(`══ ${title.replace(/\n/g, ' ')} ══`)
  await showOverlay(page, title, { section: true })
  await pause(page, 2800)
  await clearOverlay(page)
}

async function main() {
  await mkdir(VIDEO_DIR, { recursive: true })
  await enableAllDemoModules()

  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: VIDEO_DIR, size: { width: 1280, height: 720 } },
    locale: LOCALE === 'ar' ? 'ar-EG' : 'en-US',
  })
  const page = await context.newPage()
  await setLocale(page)

  try {
    // ── Customer intro on login screen ──
    await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' })
    await showOverlay(
      page,
      'فراتيلانزا\nمنصة العقارات المتكاملة',
      {
        section: true,
        subtitle: 'ERP • CRM • مبيعات • عقود • تحصيل • مالية • مقاولات • عربي كامل\nعرض تفصيلي لجميع ميزات المنصة لشركات التطوير العقاري',
      },
    )
    await pause(page, 4500)
    await clearOverlay(page)

    // Login as demo company (no super admin shown)
    await page.fill('input[type="email"]', DEMO.email)
    await page.fill('input[type="password"]', DEMO.password)
    await showOverlay(page, 'تسجيل الدخول — شركة تجريبية للتطوير العقاري', { section: false })
    await pause(page, 1200)
    await clearOverlay(page)
    await page.click('button[type="submit"]')
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 30000 })
    await pause(page, 2000)

    for (const block of TOUR) {
      if (block.introOnly) {
        await showSection(page, block.section)
        continue
      }
      await showSection(page, block.section)
      for (const p of block.pages) {
        await visitPage(page, p)
      }
    }

    await showOverlay(
      page,
      'شكراً لكم\nFRATELANZA Real Estate Platform',
      { section: true, subtitle: 'للاشتراك والاستفسار: support@fratelanza.com · rs.fratelanza.com' },
    )
    await pause(page, 4000)
  } catch (err) {
    console.error('Recording error:', err)
    await writeFile(join(OUT_DIR, 'customer-demo-error.txt'), String(err.stack || err))
  } finally {
    await page.close()
    await context.close()
    await browser.close()
  }
  console.log(`Raw video: ${VIDEO_DIR}`)
}

main()
