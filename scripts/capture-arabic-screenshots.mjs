/**
 * Arabic illustrated screenshots for marketing / docs.
 */
import { chromium } from 'playwright'
import { mkdir } from 'fs/promises'
import { join } from 'path'

const BASE_URL = process.env.DEMO_URL || 'https://rs.fratelanza.com'
const OUT_DIR = process.env.ARTIFACTS_DIR || '/opt/cursor/artifacts'
const SHOTS_DIR = join(OUT_DIR, 'arabic-screenshots')
const DEMO = { email: 'admin@demo.fratelanza.com', password: 'Demo123456' }

const SHOTS = [
  { path: '/dashboard', file: '01-dashboard', title: 'لوحة التحكم', desc: 'مؤشرات الأداء والمبيعات في لمحة واحدة' },
  { path: '/customers', file: '02-customers', title: 'إدارة العملاء', desc: 'قاعدة بيانات CRM مع استيراد ذكي' },
  { path: '/leads', file: '03-leads', title: 'مسار المبيعات', desc: 'تتبع العملاء المحتملين حتى الإغلاق' },
  { path: '/follow-ups', file: '04-followups', title: 'مكالمات المتابعة', desc: 'جدولة المكالمات وتسجيل النتائج' },
  { path: '/projects', file: '05-projects', title: 'المشاريع العقارية', desc: 'مباني ووحدات وحالة التوفر' },
  { path: '/finance', file: '06-finance', title: 'المالية', desc: 'حسابات وقيود يومية' },
  { path: '/reports', file: '07-reports', title: 'التقارير', desc: 'تصدير Excel وتحليلات' },
]

async function setArabic(page) {
  await page.addInitScript(() => {
    localStorage.setItem('language', 'ar')
    document.documentElement.lang = 'ar'
    document.documentElement.dir = 'rtl'
  })
}

async function addIllustration(page, title, desc) {
  await page.evaluate(({ title, desc }) => {
    document.getElementById('shot-illustration')?.remove()
    const wrap = document.createElement('div')
    wrap.id = 'shot-illustration'
    Object.assign(wrap.style, {
      position: 'fixed',
      top: '16px',
      right: '16px',
      zIndex: '99999',
      width: '280px',
      direction: 'rtl',
      fontFamily: 'Tahoma, Arial, sans-serif',
    })
    wrap.innerHTML = `
      <div style="background:linear-gradient(135deg,#1e3a8a,#0ea5e9);border-radius:16px;padding:16px;color:#fff;box-shadow:0 12px 40px rgba(0,0,0,.25)">
        <div style="font-size:11px;opacity:.85;margin-bottom:6px">فراتيلانزا العقارية</div>
        <div style="font-size:20px;font-weight:700;margin-bottom:8px">${title}</div>
        <div style="font-size:13px;line-height:1.5;opacity:.95">${desc}</div>
        <div style="margin-top:12px;display:flex;gap:6px">
          <span style="background:rgba(255,255,255,.2);padding:4px 10px;border-radius:999px;font-size:11px">ERP</span>
          <span style="background:rgba(255,255,255,.2);padding:4px 10px;border-radius:999px;font-size:11px">CRM</span>
          <span style="background:rgba(255,255,255,.2);padding:4px 10px;border-radius:999px;font-size:11px">عربي</span>
        </div>
      </div>
    `
    document.body.appendChild(wrap)
  }, { title, desc })
}

async function main() {
  await mkdir(SHOTS_DIR, { recursive: true })
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 }, locale: 'ar-EG' })
  const page = await context.newPage()
  await setArabic(page)

  await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' })
  await page.fill('input[type="email"]', DEMO.email)
  await page.fill('input[type="password"]', DEMO.password)
  await page.click('button[type="submit"]')
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 30000 })
  await page.waitForTimeout(1500)

  for (const shot of SHOTS) {
    console.log(`📸 ${shot.file}`)
    await page.goto(`${BASE_URL}${shot.path}`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(1500)
    await addIllustration(page, shot.title, shot.desc)
    await page.waitForTimeout(500)
    await page.screenshot({ path: join(SHOTS_DIR, `${shot.file}.png`), fullPage: false })
  }

  await browser.close()
  console.log(`Screenshots saved to ${SHOTS_DIR}`)
}

main()
