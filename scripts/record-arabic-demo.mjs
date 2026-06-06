/**
 * Arabic company-features demo video (no super admin screens).
 */
import { chromium } from 'playwright'
import { mkdir, writeFile } from 'fs/promises'
import { join } from 'path'

const BASE_URL = process.env.DEMO_URL || 'https://rs.fratelanza.com'
const OUT_DIR = process.env.ARTIFACTS_DIR || '/opt/cursor/artifacts'
const VIDEO_DIR = join(OUT_DIR, 'arabic-demo-raw')
const DEMO = { email: 'admin@demo.fratelanza.com', password: 'Demo123456' }

const PAGES = [
  ['/dashboard', 'لوحة التحكم — مؤشرات الأداء والمبيعات'],
  ['/customers', 'إدارة العملاء — قاعدة بيانات CRM'],
  ['/leads', 'مسار المبيعات — من lead إلى عقد'],
  ['/follow-ups', 'مكالمات المتابعة — جدولة وتسجيل النتائج'],
  ['/projects', 'المشاريع والوحدات — حالة التوفر'],
  ['/reservations', 'الحجوزات — حجز الوحدات'],
  ['/contracts', 'العقود — إدارة الاتفاقيات'],
  ['/collections', 'التحصيل — الأقساط والمدفوعات'],
  ['/finance', 'المالية — الحسابات والقيود'],
  ['/hr', 'الموارد البشرية — الموظفون والرواتب'],
  ['/reports', 'التقارير — تصدير Excel'],
  ['/branding', 'الهوية — شعار واسم الشركة'],
]

async function pause(page, ms = 2000) {
  await page.waitForTimeout(ms)
}

async function setArabic(page) {
  await page.addInitScript(() => {
    localStorage.setItem('language', 'ar')
    document.documentElement.lang = 'ar'
    document.documentElement.dir = 'rtl'
  })
}

async function showCaption(page, text) {
  await page.evaluate((caption) => {
    const old = document.getElementById('demo-caption')
    if (old) old.remove()
    const el = document.createElement('div')
    el.id = 'demo-caption'
    el.textContent = caption
    Object.assign(el.style, {
      position: 'fixed',
      bottom: '24px',
      left: '50%',
      transform: 'translateX(-50%)',
      zIndex: '99999',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e40af 100%)',
      color: '#fff',
      padding: '14px 28px',
      borderRadius: '12px',
      fontSize: '18px',
      fontWeight: '600',
      fontFamily: 'Tahoma, Arial, sans-serif',
      boxShadow: '0 8px 32px rgba(0,0,0,0.35)',
      maxWidth: '90%',
      textAlign: 'center',
      direction: 'rtl',
    })
    document.body.appendChild(el)
  }, text)
}

async function login(page) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' })
  await pause(page, 1000)
  await page.fill('input[type="email"]', DEMO.email)
  await page.fill('input[type="password"]', DEMO.password)
  await page.click('button[type="submit"]')
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 30000 })
  await pause(page, 1800)
}

async function main() {
  await mkdir(VIDEO_DIR, { recursive: true })
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: VIDEO_DIR, size: { width: 1280, height: 720 } },
    locale: 'ar-EG',
  })
  const page = await context.newPage()
  await setArabic(page)

  try {
    await login(page)
    for (const [path, caption] of PAGES) {
      console.log(`→ ${caption}`)
      await page.goto(`${BASE_URL}${path}`, { waitUntil: 'networkidle' })
      await showCaption(page, caption)
      await pause(page, 2800)
    }
    await pause(page, 1500)
  } catch (err) {
    console.error(err)
    await writeFile(join(OUT_DIR, 'arabic-demo-error.txt'), String(err))
  } finally {
    await page.close()
    await context.close()
    await browser.close()
  }
  console.log(`Raw Arabic video: ${VIDEO_DIR}`)
}

main()
