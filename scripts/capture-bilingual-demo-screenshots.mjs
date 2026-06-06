/**
 * Bilingual annotated screenshots — all company modules (no Super Admin).
 * Each PNG has English + Arabic feature details burned into the overlay.
 */
import { chromium } from 'playwright'
import { mkdir, writeFile } from 'fs/promises'
import { join } from 'path'

const BASE_URL = process.env.DEMO_URL || 'https://rs.fratelanza.com'
const API_BASE = `${BASE_URL}/api/v1`
const OUT_DIR = process.env.SCREENSHOTS_DIR || join(process.cwd(), 'docs', 'demo-screenshots')
const DEMO = {
  username: process.env.DEMO_USER || 'demo_admin',
  password: process.env.DEMO_PASSWORD || 'Demo123456',
  /** Production may not have username migrated yet — email still works as login */
  fallbackUsername: 'admin@demo.fratelanza.com',
}
const SUPER_ADMIN = { username: 'superadmin', email: 'admin@fratelanza.com', password: 'SuperAdmin2026' }

const ALL_MODULES = [
  'dashboard', 'customers', 'leads', 'follow_ups', 'projects', 'reservations',
  'contracts', 'collections', 'brokers', 'finance', 'hr', 'construction',
  'procurement', 'warehouse', 'property', 'customer_service', 'users',
  'reports', 'branding', 'ai_assistant',
]

/** @type {Array<{file:string, path:string, title_en:string, title_ar:string, features_en:string[], features_ar:string[], actions?:string[], scroll?:number, uiLang?:'ar'|'en'}>} */
const SHOTS = [
  {
    file: '00-login',
    path: '/login',
    title_en: 'Login — Company User',
    title_ar: 'تسجيل الدخول — مستخدم الشركة',
    features_en: [
      'Sign in with username (not email) — demo: demo_admin',
      'Bilingual interface: switch Arabic ↔ English anytime',
      'Secure JWT session for your company workspace',
      'No Super Admin access on this demo account',
    ],
    features_ar: [
      'الدخول باسم المستخدم (وليس البريد) — تجريبي: demo_admin',
      'واجهة ثنائية اللغة: التبديل بين العربية والإنجليزية',
      'جلسة آمنة لمساحة عمل شركتك فقط',
      'حساب تجريبي للشركة — بدون لوحة المشرف العام',
    ],
    uiLang: 'en',
  },
  {
    file: '01-dashboard',
    path: '/dashboard',
    title_en: 'Dashboard — Executive Overview',
    title_ar: 'لوحة التحكم — نظرة تنفيذية',
    features_en: [
      'KPI cards: total sales, collections, available units, active leads',
      'Sales trend chart and leads pipeline breakdown',
      'Action center: overdue calls, collections shortcuts',
      'Load Demo Data — fills all modules with sample records',
      'Quick links to Finance, HR, and Follow-ups',
    ],
    features_ar: [
      'بطاقات مؤشرات: المبيعات، التحصيل، الوحدات المتاحة، العملاء المحتملون',
      'رسم المبيعات وتوزيع مراحل العملاء المحتملين',
      'مركز الإجراءات: مكالمات متأخرة واختصارات التحصيل',
      'تحميل بيانات تجريبية — يملأ كل الوحدات بسجلات نموذجية',
      'روابط سريعة للمالية والموارد البشرية والمتابعات',
    ],
    scroll: 400,
  },
  {
    file: '02-customers',
    path: '/customers',
    title_en: 'Customers — Full CRM',
    title_ar: 'العملاء — إدارة علاقات كاملة',
    features_en: [
      'Stats: total customers, with contracts, reservations, linked leads',
      'Click any customer → full profile panel on the right',
      'Profile: contracts, reservations, timeline, call & WhatsApp',
      'Add / Edit customer, schedule calls, add notes, delete',
      'Bulk import from Excel/CSV with smart column mapping',
    ],
    features_ar: [
      'إحصائيات: إجمالي العملاء، العقود، الحجوزات، الربط بالعملاء المحتملين',
      'اضغط أي عميل → ملف كامل في اللوحة اليمنى',
      'الملف: العقود، الحجوزات، السجل، اتصال وواتساب',
      'إضافة / تعديل، جدولة مكالمات، ملاحظات، حذف',
      'استيراد جماعي من Excel/CSV مع مطابقة الأعمدة تلقائياً',
    ],
  },
  {
    file: '03-leads-kanban',
    path: '/leads',
    title_en: 'Leads — Sales Pipeline (Kanban)',
    title_ar: 'العملاء المحتملون — مسار المبيعات',
    features_en: [
      'Professional Kanban: New → Contacted → Interested → … → Contract',
      'Drag-style stage moves with forward/back chevrons',
      'Lead score badges and source tracking',
      'Add / Edit / Delete leads; schedule follow-up calls',
      'Switch to List view for spreadsheet-style filtering',
    ],
    features_ar: [
      'كانبان احترافي: جديد → تم التواصل → مهتم → … → عقد',
      'نقل بين المراحل للأمام والخلف مع أزرار واضحة',
      'شارات التقييم وتتبع مصدر العميل المحتمل',
      'إضافة / تعديل / حذف وجدولة مكالمات متابعة',
      'التبديل لعرض القائمة للفرز والبحث',
    ],
    actions: ['leads-list'],
  },
  {
    file: '04-leads-list',
    path: '/leads',
    title_en: 'Leads — List View',
    title_ar: 'العملاء المحتملون — عرض القائمة',
    features_en: [
      'Sortable table with export to Excel',
      'Columns: name, mobile, stage, score, source, next follow-up',
      'Row actions: edit, delete, move stage',
      'Connected to Customers when converted',
    ],
    features_ar: [
      'جدول قابل للفرز مع تصدير Excel',
      'أعمدة: الاسم، الجوال، المرحلة، التقييم، المصدر، المتابعة القادمة',
      'إجراءات الصف: تعديل، حذف، نقل المرحلة',
      'مرتبط بسجل العميل عند التحويل',
    ],
    actions: ['leads-list-only'],
  },
  {
    file: '05-follow-ups-queue',
    path: '/follow-ups',
    title_en: 'Follow-ups — Call Queue',
    title_ar: 'المتابعات — قائمة المكالمات',
    features_en: [
      'Today & overdue call counts with upcoming week preview',
      'Click a call → dial, WhatsApp, complete, reschedule',
      'Log call outcome and auto-schedule next follow-up',
      'Customer activity timeline on the detail panel',
      'Schedule new calls linked to customers or leads',
    ],
    features_ar: [
      'عدادات مكالمات اليوم والمتأخرة ومعاينة الأسبوع',
      'اضغط مكالمة → اتصال، واتساب، إتمام، إعادة جدولة',
      'تسجيل نتيجة المكالمة وجدولة المتابعة التالية',
      'سجل نشاط العميل في لوحة التفاصيل',
      'جدولة مكالمات جديدة مرتبطة بالعملاء أو المحتملين',
    ],
    actions: ['followups-queue'],
  },
  {
    file: '06-follow-ups-history',
    path: '/follow-ups',
    title_en: 'Follow-ups — Call History',
    title_ar: 'المتابعات — سجل المكالمات',
    features_en: [
      'Completed calls with outcome labels (interested, callback, no answer)',
      'Outcome notes preserved for CRM history',
      'Delete reminders when no longer needed',
    ],
    features_ar: [
      'المكالمات المكتملة مع نتائج (مهتم، معاودة، لم يرد)',
      'حفظ ملاحظات النتيجة في سجل CRM',
      'حذف التذكيرات غير المطلوبة',
    ],
    actions: ['followups-history'],
  },
  {
    file: '07-projects-overview',
    path: '/projects',
    title_en: 'Projects — Overview & Stats',
    title_ar: 'المشاريع — نظرة عامة وإحصائيات',
    features_en: [
      'Tabs: Overview, Units Board, Projects List, Units',
      'Stat cards: projects count, available/reserved/total units',
      'Add projects and units from the header',
      'Central hub for real estate inventory',
    ],
    features_ar: [
      'تبويبات: نظرة عامة، لوحة الوحدات، قائمة المشاريع، الوحدات',
      'بطاقات: عدد المشاريع، المتاحة/المحجوزة/الإجمالي',
      'إضافة مشاريع ووحدات من الأعلى',
      'مركز إدارة مخزون العقارات',
    ],
    actions: ['projects-overview'],
  },
  {
    file: '08-projects-units-board',
    path: '/projects',
    title_en: 'Projects — Units Board',
    title_ar: 'المشاريع — لوحة الوحدات',
    features_en: [
      'Visual grid: available, reserved, contracted, sold units',
      'Click available unit → create reservation instantly',
      'Color-coded status per unit code and floor',
      'Linked to Reservations and Contracts modules',
    ],
    features_ar: [
      'شبكة مرئية: متاح، محجوز، متعاقد، مباع',
      'اضغط وحدة متاحة → إنشاء حجز فوراً',
      'ألوان حسب الحالة ورقم الوحدة والدور',
      'مرتبط بوحدات الحجوزات والعقود',
    ],
    actions: ['projects-board'],
  },
  {
    file: '09-reservations',
    path: '/reservations',
    title_en: 'Reservations',
    title_ar: 'الحجوزات',
    features_en: [
      'Book units with deposit and expiry dates',
      'Approve pending reservations',
      'Convert approved reservation → sales contract',
      'Edit / Delete reservation records',
      'Links customer, unit, and broker',
    ],
    features_ar: [
      'حجز الوحدات مع العربون وتاريخ الانتهاء',
      'اعتماد الحجوزات المعلقة',
      'تحويل الحجز المعتمد → عقد بيع',
      'تعديل / حذف سجلات الحجز',
      'يربط العميل والوحدة والوسيط',
    ],
  },
  {
    file: '10-contracts',
    path: '/contracts',
    title_en: 'Contracts — Sales Agreements',
    title_ar: 'العقود — اتفاقيات البيع',
    features_en: [
      'Contract number, customer, unit, total price, status',
      'Payment plan drives Collections installments',
      'Edit / Delete contracts',
      'Export table to Excel',
    ],
    features_ar: [
      'رقم العقد، العميل، الوحدة، السعر، الحالة',
      'خطة الدفع تولّد أقساط التحصيل',
      'تعديل / حذف العقود',
      'تصدير الجدول إلى Excel',
    ],
  },
  {
    file: '11-collections',
    path: '/collections',
    title_en: 'Collections — Installments',
    title_ar: 'التحصيل — الأقساط',
    features_en: [
      'Installment schedule per contract with due dates',
      'Record payments → updates paid & remaining balance',
      'Overdue status highlighted for collection officers',
      'Linked to customer name and unit code',
    ],
    features_ar: [
      'جدول أقساط لكل عقد مع تواريخ الاستحقاق',
      'تسجيل الدفعات → تحديث المدفوع والمتبقي',
      'تمييز المتأخرات لمسؤولي التحصيل',
      'مرتبط باسم العميل ورمز الوحدة',
    ],
  },
  {
    file: '12-brokers',
    path: '/brokers',
    title_en: 'Brokers — Partners & Commissions',
    title_ar: 'الوسطاء — الشركاء والعمولات',
    features_en: [
      'Broker directory with mobile, email, commission %',
      'Rank score for performance tracking',
      'Add / Edit / Delete broker records',
      'Assign brokers on reservations and sales',
    ],
    features_ar: [
      'دليل الوسطاء مع الجوال والبريد ونسبة العمولة',
      'تقييم الأداء للترتيب',
      'إضافة / تعديل / حذف الوسطاء',
      'ربط الوسطاء بالحجوزات والمبيعات',
    ],
  },
  {
    file: '13-construction',
    path: '/construction',
    title_en: 'Construction — Project Phases',
    title_ar: 'المقاولات — مراحل المشروع',
    features_en: [
      'Phases: planned dates, progress %, planned vs actual cost',
      'Track structure, finishing, MEP milestones',
      'Add / Edit / Delete construction phases',
      'Tied to real estate projects',
    ],
    features_ar: [
      'مراحل: تواريخ مخططة، نسبة الإنجاز، التكلفة الفعلية/المخططة',
      'متابعة الهيكل والتشطيبات والمرافق',
      'إضافة / تعديل / حذف المراحل',
      'مرتبط بمشاريع التطوير العقاري',
    ],
  },
  {
    file: '14-procurement',
    path: '/procurement',
    title_en: 'Procurement — Vendors',
    title_ar: 'المشتريات — الموردون',
    features_en: [
      'Vendor list with contact person, phone, rating',
      'Manage suppliers for construction materials',
      'Add / Edit / Delete vendors',
      'Supports warehouse replenishment workflow',
    ],
    features_ar: [
      'قائمة الموردين مع جهة الاتصال والهاتف والتقييم',
      'إدارة موردي مواد البناء',
      'إضافة / تعديل / حذف الموردين',
      'يدعم سير عمل تعبئة المستودع',
    ],
  },
  {
    file: '15-warehouse-inventory',
    path: '/warehouse',
    title_en: 'Warehouse — Inventory (Stock)',
    title_ar: 'المستودع — المخزون',
    features_en: [
      'Inventory tab shows ALL stock: cement, steel, tiles…',
      'Each item: SKU, quantity, unit, warehouse location',
      'Low-stock alerts when quantity ≤ minimum level',
      'Add / Edit / Delete inventory items',
      'Warehouses = locations; Inventory = materials inside them',
    ],
    features_ar: [
      'تبويب المخزون يعرض كل المواد: أسمنت، حديد، بلاط…',
      'كل صنف: SKU، الكمية، الوحدة، موقع المستودع',
      'تنبيهات نقص المخزون عند الوصول للحد الأدنى',
      'إضافة / تعديل / حذف أصناف المخزون',
      'المستودعات = المواقع؛ المخزون = المواد داخلها',
    ],
    actions: ['warehouse-inventory'],
  },
  {
    file: '16-warehouse-locations',
    path: '/warehouse',
    title_en: 'Warehouse — Storage Locations',
    title_ar: 'المستودع — مواقع التخزين',
    features_en: [
      'Define physical stores: main depot, site store, codes',
      'Location address for each warehouse',
      'Add / Edit / Deactivate warehouses',
    ],
    features_ar: [
      'تعريف مخازن فعلية: المستودع الرئيسي، مخزن الموقع',
      'عنوان كل موقع تخزين',
      'إضافة / تعديل / إيقاف المستودعات',
    ],
    actions: ['warehouse-locations'],
  },
  {
    file: '17-property-management',
    path: '/property',
    title_en: 'Property Management — After Handover',
    title_ar: 'إدارة الممتلكات — بعد التسليم',
    features_en: [
      'For sold/delivered units: AC, plumbing, doors issues',
      'Maintenance requests linked to unit + owner customer',
      'Priority & status: open → in progress → completed',
      'Step-by-step guide shown on screen',
      'Add / Edit / Delete maintenance tickets',
    ],
    features_ar: [
      'للوحدات المباعة/المسلّمة: أعطال تكييف، سباكة، أبواب',
      'طلبات صيانة مرتبطة بالوحدة والعميل المالك',
      'الأولوية والحالة: مفتوح → قيد التنفيذ → مكتمل',
      'دليل خطوة بخطوة معروض في الصفحة',
      'إضافة / تعديل / حذف طلبات الصيانة',
    ],
  },
  {
    file: '18-finance',
    path: '/finance',
    title_en: 'Finance — P&L, Cash, Accounts',
    title_ar: 'المالية — الأرباح والنقد والحسابات',
    features_en: [
      'Overview: sales, collections, overdue, cash position',
      'Tabs: Trial Balance, P&L, Cash, Journal, Chart of Accounts',
      'Quick links to Collections and Contracts',
      'Export financial reports to Excel',
      'Delete chart-of-account entries when needed',
    ],
    features_ar: [
      'نظرة عامة: المبيعات، التحصيل، المتأخرات، النقد',
      'تبويبات: ميزان مراجعة، أرباح وخسائر، نقدية، قيود، دليل حسابات',
      'روابط سريعة للتحصيل والعقود',
      'تصدير التقارير المالية إلى Excel',
      'حذف حسابات من دليل الحسابات عند الحاجة',
    ],
    scroll: 300,
  },
  {
    file: '19-hr-employees',
    path: '/hr',
    title_en: 'HR — Employees & Payroll',
    title_ar: 'الموارد البشرية — الموظفون والرواتب',
    features_en: [
      'Employee cards: code, department, salary',
      'Generate monthly payroll (11% social insurance Egypt)',
      'Leaves: request, approve, delete',
      'Attendance: check-in/out records',
      'Delete employees when offboarded',
    ],
    features_ar: [
      'بطاقات الموظفين: الكود، القسم، الراتب',
      'إنشاء كشف رواتب شهري (تأمينات 11٪ مصر)',
      'الإجازات: طلب، اعتماد، حذف',
      'الحضور: سجلات الدخول والخروج',
      'حذف الموظفين عند انتهاء الخدمة',
    ],
    actions: ['hr-employees'],
  },
  {
    file: '20-hr-payslips',
    path: '/hr',
    title_en: 'HR — Payslips',
    title_ar: 'الموارد البشرية — كشوف الرواتب',
    features_en: [
      'Dedicated Payslips tab — all employees, all months',
      'Columns: basic salary, insurance deduction, net pay',
      'Export payslips to Excel for bank transfer',
      'Generated from payroll runs per month',
    ],
    features_ar: [
      'تبويب كشوف الرواتب — كل الموظفين وكل الشهور',
      'أعمدة: الراتب الأساسي، التأمينات، الصافي',
      'تصدير كشوف الرواتب إلى Excel للتحويل البنكي',
      'تُنشأ من مسيرات الرواتب الشهرية',
    ],
    actions: ['hr-payslips'],
  },
  {
    file: '21-reports',
    path: '/reports',
    title_en: 'Reports — Analytics Center',
    title_ar: 'التقارير — مركز التحليلات',
    features_en: [
      '20+ real estate reports: inventory, sales, collections, CRM',
      'Sortable tables with search and filters',
      'One-click Excel export per report',
      'Categories: Inventory, Sales, Finance, HR, Operations',
    ],
    features_ar: [
      'أكثر من 20 تقريراً عقارياً: مخزون، مبيعات، تحصيل، CRM',
      'جداول قابلة للفرز مع بحث وفلاتر',
      'تصدير Excel بنقرة واحدة لكل تقرير',
      'فئات: المخزون، المبيعات، المالية، الموارد البشرية، العمليات',
    ],
    scroll: 350,
  },
  {
    file: '22-ai-assistant',
    path: '/ai-assistant',
    title_en: 'AI Assistant — Business Insights',
    title_ar: 'المساعد الذكي — رؤى الأعمال',
    features_en: [
      'Ask questions in Arabic or English about your data',
      'Sales performance, collections, overdue analysis',
      'Natural language queries — no report builder needed',
      'Powered by company-scoped data only',
    ],
    features_ar: [
      'اسأل بالعربية أو الإنجليزية عن بيانات شركتك',
      'أداء المبيعات، التحصيل، تحليل المتأخرات',
      'استعلامات بلغة طبيعية — بدون بناء تقارير معقدة',
      'يعمل على بيانات شركتك فقط',
    ],
  },
  {
    file: '23-customer-service',
    path: '/customer-service',
    title_en: 'Customer Service — Support Tickets',
    title_ar: 'خدمة العملاء — تذاكر الدعم',
    features_en: [
      'Ticket number, subject, customer, category, priority',
      'Track open → resolved support requests',
      'Add / Edit / Delete tickets',
      'Separate from post-handover maintenance (Property module)',
    ],
    features_ar: [
      'رقم التذكرة، الموضوع، العميل، الفئة، الأولوية',
      'متابعة الطلبات من مفتوح → محلول',
      'إضافة / تعديل / حذف التذاكر',
      'منفصل عن صيانة ما بعد التسليم (إدارة الممتلكات)',
    ],
  },
  {
    file: '24-team-users',
    path: '/users',
    title_en: 'Team Users — Roles & Access',
    title_ar: 'مستخدمي الفريق — الأدوار والصلاحيات',
    features_en: [
      'Company users with username, Arabic/English name, role',
      'Roles: sales, collection, accountant, HR, admin…',
      'Add users, delete deactivated accounts',
      'Module access controlled by subscription plan',
    ],
    features_ar: [
      'مستخدمو الشركة: اسم مستخدم، اسم عربي/إنجليزي، دور',
      'أدوار: مبيعات، تحصيل، محاسبة، موارد بشرية، مدير…',
      'إضافة مستخدمين وحذف الحسابات المعطلة',
      'صلاحية الوحدات حسب خطة الاشتراك',
    ],
  },
  {
    file: '25-branding',
    path: '/branding',
    title_en: 'Branding — Your Company Identity',
    title_ar: 'الهوية البصرية — هوية شركتك',
    features_en: [
      'Upload company logo shown across the platform',
      'Customize company display name',
      'White-label feel for your tenants and staff',
    ],
    features_ar: [
      'رفع شعار الشركة المعروض في المنصة',
      'تخصيص اسم العرض للشركة',
      'مظهر خاص بعلامتكم لفريقكم وعملائكم',
    ],
  },
]

async function pause(page, ms) {
  await page.waitForTimeout(ms)
}

async function setUiLang(page, lang) {
  await page.evaluate((l) => {
    localStorage.setItem('language', l)
    localStorage.setItem('i18nextLng', l)
    document.documentElement.lang = l
    document.documentElement.dir = l === 'ar' ? 'rtl' : 'ltr'
  }, lang)
}

async function addBilingualPanel(page, shot) {
  const bulletsEn = shot.features_en.map((f) => `<li>${f}</li>`).join('')
  const bulletsAr = shot.features_ar.map((f) => `<li>${f}</li>`).join('')
  await page.evaluate(({ title_en, title_ar, bulletsEn, bulletsAr }) => {
    document.getElementById('bilingual-panel')?.remove()
    const panel = document.createElement('div')
    panel.id = 'bilingual-panel'
    Object.assign(panel.style, {
      position: 'fixed',
      bottom: '12px',
      left: '12px',
      right: '12px',
      zIndex: '99999',
      maxHeight: '42vh',
      overflow: 'auto',
      fontFamily: 'Tahoma, Arial, sans-serif',
      boxShadow: '0 16px 48px rgba(0,0,0,.35)',
      borderRadius: '14px',
    })
    panel.innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:0;background:#0f172a;color:#fff;border-radius:14px;overflow:hidden">
        <div style="padding:14px 16px;border-right:1px solid rgba(255,255,255,.15)">
          <div style="font-size:10px;letter-spacing:1px;opacity:.7;margin-bottom:4px">ENGLISH</div>
          <div style="font-size:16px;font-weight:700;margin-bottom:8px;color:#38bdf8">${title_en}</div>
          <ul style="margin:0;padding-left:18px;font-size:11px;line-height:1.55;opacity:.95">${bulletsEn}</ul>
        </div>
        <div style="padding:14px 16px;direction:rtl;text-align:right">
          <div style="font-size:10px;letter-spacing:1px;opacity:.7;margin-bottom:4px">العربية</div>
          <div style="font-size:16px;font-weight:700;margin-bottom:8px;color:#fbbf24">${title_ar}</div>
          <ul style="margin:0;padding-right:18px;font-size:11px;line-height:1.55;opacity:.95">${bulletsAr}</ul>
        </div>
      </div>
      <div style="text-align:center;margin-top:6px;font-size:10px;color:#64748b;font-weight:600">FRATELANZA · Customer Demo · demo_admin</div>
    `
    document.body.appendChild(panel)
  }, { title_en: shot.title_en, title_ar: shot.title_ar, bulletsEn, bulletsAr })
}

async function removePanel(page) {
  await page.evaluate(() => document.getElementById('bilingual-panel')?.remove())
}

async function enableAllDemoModules() {
  for (const creds of [
    { username: SUPER_ADMIN.username, password: SUPER_ADMIN.password },
    { email: SUPER_ADMIN.email, password: SUPER_ADMIN.password },
  ]) {
    try {
      const loginRes = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(creds),
      })
      if (!loginRes.ok) continue
      const { access_token } = await loginRes.json()
      const companiesRes = await fetch(`${API_BASE}/super-admin/companies?page_size=100`, {
        headers: { Authorization: `Bearer ${access_token}` },
      })
      const companies = await companiesRes.json()
      const demo = companies.items?.find((c) => c.code === 'DEMO')
      if (!demo) continue
      await fetch(`${API_BASE}/modules/company/${demo.id}`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${access_token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled_modules: ALL_MODULES }),
      })
      console.log(`✓ All ${ALL_MODULES.length} modules enabled for DEMO`)
      return access_token
    } catch {
      /* try next creds */
    }
  }
  return null
}

async function loginDemo(page) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle', timeout: 60000 })
  const userInput = page.locator('input[autocomplete="username"], input[type="text"], input[type="email"]').first()
  const tryLogin = async (user) => {
    await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle', timeout: 60000 })
    await userInput.fill(user)
    await page.fill('input[type="password"]', DEMO.password)
    await page.click('button[type="submit"]')
    try {
      await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 12000 })
      return true
    } catch {
      return false
    }
  }
  const ok = (await tryLogin(DEMO.username)) || (await tryLogin(DEMO.fallbackUsername))
  if (!ok) throw new Error('Demo login failed — check DEMO_USER / DEMO_PASSWORD')
  await pause(page, 2000)
  try {
    await page.request.post(`${API_BASE}/dashboard/reseed-demo`, {
      headers: { Authorization: `Bearer ${await page.evaluate(() => localStorage.getItem('access_token') || '')}` },
    })
  } catch {
    const token = await page.evaluate(() => {
      try {
        const raw = localStorage.getItem('auth-storage')
        return raw ? JSON.parse(raw)?.state?.accessToken : null
      } catch { return null }
    })
    if (token) {
      await fetch(`${API_BASE}/dashboard/reseed-demo`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => {})
    }
  }
  await pause(page, 1500)
}

async function runActions(page, actions = []) {
  for (const action of actions) {
    switch (action) {
      case 'leads-list': {
        const btn = page.getByRole('button', { name: /list|قائمة|kanban/i })
        if (await btn.count()) {
          const listBtn = page.getByRole('button', { name: /^list|^قائمة/i })
          if (await listBtn.count()) await listBtn.first().click()
        }
        await pause(page, 1500)
        break
      }
      case 'leads-list-only': {
        const listBtn = page.getByRole('button', { name: /list|قائمة/i })
        if (await listBtn.count()) await listBtn.first().click()
        await pause(page, 1800)
        break
      }
      case 'followups-history': {
        const tab = page.getByRole('button', { name: /history|السجل|سجل/i })
        if (await tab.count()) await tab.first().click()
        await pause(page, 1800)
        break
      }
      case 'followups-queue': {
        const tab = page.getByRole('button', { name: /queue|قائمة|انتظار/i })
        if (await tab.count()) await tab.first().click()
        await pause(page, 1200)
        break
      }
      case 'projects-overview': {
        const tab = page.getByRole('button', { name: /overview|نظرة/i })
        if (await tab.count()) await tab.first().click()
        await pause(page, 1500)
        break
      }
      case 'projects-board': {
        const tab = page.getByRole('button', { name: /board|لوحة/i })
        if (await tab.count()) await tab.first().click()
        await pause(page, 1800)
        break
      }
      case 'warehouse-inventory': {
        const tab = page.getByRole('button', { name: /inventory|مخزون/i })
        if (await tab.count()) await tab.first().click()
        await pause(page, 1800)
        break
      }
      case 'warehouse-locations': {
        const tab = page.getByRole('button', { name: /location|مواقع|warehouse/i })
        if (await tab.count()) {
          const loc = page.getByRole('button', { name: /location|مواقع/i })
          if (await loc.count()) await loc.first().click()
          else await tab.first().click()
        }
        await pause(page, 1800)
        break
      }
      case 'hr-employees': {
        const tab = page.getByRole('button', { name: /employee|موظف/i })
        if (await tab.count()) await tab.first().click()
        await pause(page, 1500)
        break
      }
      case 'hr-payslips': {
        const tab = page.getByRole('button', { name: /payslip|رواتب|كشف/i })
        if (await tab.count()) await tab.first().click()
        await pause(page, 1800)
        break
      }
    }
  }
}

async function captureShot(page, shot) {
  console.log(`📸 ${shot.file}`)
  const lang = shot.uiLang || 'ar'
  await setUiLang(page, lang)
  if (shot.path !== '/login') {
    await page.goto(`${BASE_URL}${shot.path}`, { waitUntil: 'networkidle', timeout: 60000 })
  } else {
    await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle', timeout: 60000 })
  }
  await pause(page, 1200)
  if (shot.path === '/customers') {
    const first = page.locator('button.rounded-xl.border').first()
    if (await first.count()) {
      await first.click().catch(() => {})
      await pause(page, 1000)
    }
  }
  await runActions(page, shot.actions)
  if (shot.scroll) {
    await page.evaluate((y) => window.scrollBy({ top: y, behavior: 'instant' }), shot.scroll)
    await pause(page, 600)
  }
  await addBilingualPanel(page, shot)
  await pause(page, 400)
  await page.screenshot({
    path: join(OUT_DIR, `${shot.file}.png`),
    fullPage: false,
  })
  await removePanel(page)
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true })
  await enableAllDemoModules()

  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    locale: 'ar-EG',
    deviceScaleFactor: 1,
  })
  const page = await context.newPage()

  const manifest = []
  try {
    await loginDemo(page)
    for (const shot of SHOTS) {
      if (shot.path === '/login') {
        await setUiLang(page, shot.uiLang || 'en')
        await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' })
        await pause(page, 1000)
        await addBilingualPanel(page, shot)
        await page.screenshot({ path: join(OUT_DIR, `${shot.file}.png`) })
        await removePanel(page)
      } else {
        await captureShot(page, shot)
      }
      manifest.push({
        file: `${shot.file}.png`,
        path: shot.path,
        title_en: shot.title_en,
        title_ar: shot.title_ar,
        features_en: shot.features_en,
        features_ar: shot.features_ar,
      })
    }
  } catch (err) {
    console.error(err)
    await writeFile(join(OUT_DIR, 'capture-error.txt'), String(err.stack || err))
    throw err
  } finally {
    await browser.close()
  }

  await writeFile(join(OUT_DIR, 'manifest.json'), JSON.stringify(manifest, null, 2))
  console.log(`\n✅ ${manifest.length} screenshots → ${OUT_DIR}`)
}

main()
