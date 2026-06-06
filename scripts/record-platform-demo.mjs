/**
 * Records a walkthrough video of the FRATELANZA platform.
 * Usage: node scripts/record-platform-demo.mjs
 */
import { chromium } from 'playwright'
import { mkdir, writeFile } from 'fs/promises'
import { join } from 'path'

const BASE_URL = process.env.DEMO_URL || 'https://rs.fratelanza.com'
const OUT_DIR = process.env.ARTIFACTS_DIR || '/opt/cursor/artifacts'
const VIDEO_DIR = join(OUT_DIR, 'demo-video-raw')

const SUPER_ADMIN = { email: 'admin@fratelanza.com', password: 'SuperAdmin2026' }
const DEMO_COMPANY = { email: 'admin@demo.fratelanza.com', password: 'Demo123456' }

async function pause(page, ms = 1800) {
  await page.waitForTimeout(ms)
}

async function login(page, { email, password }) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' })
  await pause(page, 1200)
  await page.fill('input[type="email"]', email)
  await page.fill('input[type="password"]', password)
  await page.click('button[type="submit"]')
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 30000 })
  await pause(page, 2000)
}

async function logout(page) {
  const logoutBtn = page.getByRole('button', { name: /logout|تسجيل الخروج/i })
  if (await logoutBtn.count()) {
    await logoutBtn.first().click()
    await page.waitForURL('**/login**', { timeout: 15000 }).catch(() => {})
    await pause(page, 1500)
  }
}

async function visit(page, path, label) {
  console.log(`→ ${label}`)
  await page.goto(`${BASE_URL}${path}`, { waitUntil: 'networkidle' })
  await pause(page, 2200)
}

async function main() {
  await mkdir(VIDEO_DIR, { recursive: true })

  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: VIDEO_DIR, size: { width: 1280, height: 720 } },
    locale: 'en-US',
  })
  const page = await context.newPage()

  try {
    // Super Admin tour
    await login(page, SUPER_ADMIN)
    await visit(page, '/super-admin', 'Super Admin Dashboard')
    await visit(page, '/super-admin/companies', 'Companies')
    await visit(page, '/super-admin/users', 'Users')
    await visit(page, '/super-admin/subscriptions', 'Subscription Plans')
    await visit(page, '/super-admin/settings', 'Settings')
    await logout(page)

    // Company admin tour
    await login(page, DEMO_COMPANY)
    const companyPages = [
      ['/dashboard', 'Company Dashboard'],
      ['/customers', 'Customers & CRM'],
      ['/leads', 'Leads Pipeline'],
      ['/follow-ups', 'Follow-up Calls'],
      ['/projects', 'Projects & Units'],
      ['/reservations', 'Reservations'],
      ['/contracts', 'Contracts'],
      ['/finance', 'Finance'],
      ['/hr', 'Human Resources'],
      ['/reports', 'Reports & Analytics'],
      ['/branding', 'Company Branding'],
    ]
    for (const [path, label] of companyPages) {
      await visit(page, path, label)
    }
    await pause(page, 2000)
  } catch (err) {
    console.error('Recording error:', err)
    await writeFile(join(OUT_DIR, 'demo-recording-error.txt'), String(err))
  } finally {
    await page.close()
    await context.close()
    await browser.close()
  }

  console.log(`Raw video saved under ${VIDEO_DIR}`)
}

main()
