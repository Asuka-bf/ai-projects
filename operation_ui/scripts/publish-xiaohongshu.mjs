import puppeteer from 'puppeteer'
import { readFileSync } from 'fs'

const CREATOR_IMG_NOTE_URL = 'https://creator.xiaohongshu.com/publish/imgNote'

function loadPayload(payloadPath) {
  const raw = readFileSync(payloadPath, 'utf8')
  return JSON.parse(raw)
}

function parseCookieString(cookieStr) {
  if (!cookieStr) return []
  return cookieStr.split(';').map(c => {
    const [name, ...rest] = c.trim().split('=')
    return {
      name,
      value: rest.join('='),
      domain: '.xiaohongshu.com',
      path: '/',
    }
  })
}

async function run(payloadPath) {
  const payload = loadPayload(payloadPath)
  // 优先用 payload 中的 cookie，为空时使用环境变量 XIAOHONGSHU_COOKIE（打开页面时赋值）
  const cookieStr = (payload.cookie || process.env.XIAOHONGSHU_COOKIE || '').trim()

  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: null,
    args: [
      '--start-maximized',
      '--no-sandbox',
      '--disable-setuid-sandbox'
    ],
  })

  const page = await browser.newPage()

  await page.setUserAgent(
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  )

  // 1️⃣ 先打开主域名
  await page.goto('https://www.xiaohongshu.com', {
    waitUntil: 'domcontentloaded'
  })

  // 2️⃣ 注入 cookie
  const cookies = parseCookieString(cookieStr)
  if (cookies.length) {
    await page.setCookie(...cookies)
  }

  // 3️⃣ 再跳转创作者页面
  await page.goto(CREATOR_IMG_NOTE_URL, {
    waitUntil: 'networkidle2'
  })

  console.log(JSON.stringify({ success: true, message: '已打开小红书发布页' }))
}

run(process.argv[2])