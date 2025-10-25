import fs from 'node:fs/promises'
import path from 'node:path'
import {chromium, devices} from 'playwright'

const baseHost = 'https://telegram-feedback-bot.localhost'
const outputDir = path.resolve('artifacts/playwright')

await fs.mkdir(outputDir, {recursive: true})

const shotFilenames = [
    'app-dashboard-mobile.png',
    'app-bot-detail-mobile.png',
    'app-add-bot-mobile.png',
    'app-add-user-mobile.png'
]
for (const file of shotFilenames) {
    await fs.rm(path.join(outputDir, file), {force: true})
}

const browser = await chromium.launch()
const context = await browser.newContext({
    ...devices['iPhone 14 Pro'],
    ignoreHTTPSErrors: true
})

const page = await context.newPage()

async function redactVisibleContent() {
    await page.evaluate(() => {
        const usernameRegex = /@[A-Za-z0-9_]+/g
        const idRegex = /\b\d{7,}\b/g

        const replaceText = value =>
            value
                ? value.replace(usernameRegex, '@redacted').replace(idRegex, 'ID-REDACTED')
                : value

        const botButtons = Array.from(
            document.querySelectorAll(
                'button[aria-label^="Open bot"], button[aria-label^="Open Bot"]'
            )
        )
        botButtons.forEach((button, index) => {
            button.setAttribute('aria-label', `Open bot Bot ${index + 1}`)
            const title = button.querySelector('h3')
            if (title) title.textContent = `Bot ${index + 1}`
            const subtitle = button.querySelector('p')
            if (subtitle) subtitle.textContent = `@bot_${index + 1}`
        })

        const userButtons = Array.from(
            document.querySelectorAll('button[aria-label^="Manage user"]')
        )
        userButtons.forEach((button, index) => {
            button.setAttribute('aria-label', `Manage user User ${index + 1}`)
            const title = button.querySelector('h3')
            if (title) title.textContent = `@user_${index + 1}`
            const subtitle = button.querySelector('p')
            if (subtitle) subtitle.textContent = 'ID-REDACTED'
        })

        document.querySelectorAll('a[href^="https://t.me/"]').forEach((anchor, idx) => {
            anchor.textContent = `@redacted_${idx + 1}`
            anchor.setAttribute('href', `https://t.me/redacted_${idx + 1}`)
        })

        document.querySelectorAll('[aria-label]').forEach(element => {
            const current = element.getAttribute('aria-label')
            if (!current) return
            element.setAttribute('aria-label', replaceText(current))
        })

        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)
        const nodes = []
        while (walker.nextNode()) nodes.push(walker.currentNode)
        nodes.forEach(node => {
            if (!node.nodeValue) return
            if (node.parentElement && ['SCRIPT', 'STYLE'].includes(node.parentElement.tagName))
                return
            node.nodeValue = replaceText(node.nodeValue)
        })

        document.querySelectorAll('input, textarea').forEach(input => {
            if (typeof input.value === 'string') {
                input.value = replaceText(input.value)
            }
            const placeholder = input.getAttribute('placeholder')
            if (placeholder) {
                input.setAttribute('placeholder', replaceText(placeholder))
            }
        })
    })
}

async function captureSection(filename) {
    await redactVisibleContent()
    await page.locator('main').screenshot({path: path.join(outputDir, filename)})
}

async function waitForMain() {
    await page.waitForSelector('main', {state: 'visible', timeout: 60000})
}

async function captureDashboard() {
    await page.goto(`${baseHost}/app`, {waitUntil: 'networkidle'})
    await waitForMain()
    await page.waitForTimeout(800)
    await captureSection('app-dashboard-mobile.png')
}

async function captureBotDetail() {
    const botLocator = page.locator('button[aria-label^="Open bot"]')
    if ((await botLocator.count()) === 0) return
    await botLocator.first().scrollIntoViewIfNeeded()
    await botLocator.first().click()
    await page.waitForURL('**/app/bot/**', {timeout: 10000})
    await waitForMain()
    await page.waitForTimeout(800)
    await captureSection('app-bot-detail-mobile.png')
}

async function captureAddBot() {
    await page.goto(`${baseHost}/app/add_bot`, {waitUntil: 'networkidle'})
    await waitForMain()
    await page.waitForTimeout(800)
    await captureSection('app-add-bot-mobile.png')
}

async function captureAddUser() {
    await page.goto(`${baseHost}/app/add_user`, {waitUntil: 'networkidle'})
    await waitForMain()
    await page.waitForTimeout(800)
    await captureSection('app-add-user-mobile.png')
}

try {
    await captureDashboard()
    await captureBotDetail()
    await captureAddBot()
    await captureAddUser()
} finally {
    await browser.close()
}
