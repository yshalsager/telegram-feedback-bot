import {derived, get, writable} from 'svelte/store'
import {locales as supportedLocales} from 'virtual:wuchale/locales'
import {loadLocale} from 'wuchale/load-utils'
import './wuchale-loader.svelte.js'

const STORAGE_KEY = 'telegram_feedback_bot.locale'
const DEFAULT_LOCALE = supportedLocales[0] ?? 'en'

export const locale = writable(DEFAULT_LOCALE)
export const locales = supportedLocales
export const availableLocales = derived(locale, (current: string) => {
    const formatter = new Intl.DisplayNames([current], {type: 'language'})
    return supportedLocales.map(locale => ({
        locale,
        name: formatter.of(locale) ?? locale
    }))
})

locale.subscribe(value => {
    if (typeof document === 'undefined') return
    document.documentElement.lang = value
    document.documentElement.dir = value.startsWith('ar') ? 'rtl' : 'ltr'
})

function isValidLocale(locale: string | null | undefined): locale is string {
    return typeof locale === 'string' && supportedLocales.includes(locale)
}

export async function applyLocale(newLocale: string) {
    if (!isValidLocale(newLocale)) return

    if (typeof window === 'undefined') {
        locale.set(newLocale)
        return
    }

    await loadLocale(newLocale)
    locale.set(newLocale)
    localStorage.setItem(STORAGE_KEY, newLocale)
}

export async function initLocale(preferred?: string | null) {
    const stored = typeof window !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null

    if (isValidLocale(stored)) {
        await applyLocale(stored)
        return get(locale)
    }

    if (isValidLocale(preferred)) {
        await applyLocale(preferred)
        return get(locale)
    }

    await applyLocale(DEFAULT_LOCALE)
    return get(locale)
}

export function formatNumber(value: number, localeOverride?: string) {
    const targetLocale = localeOverride ?? get(locale)
    return new Intl.NumberFormat(targetLocale).format(value)
}

export function formatCharacterCount(count: number, limit = 4096, localeOverride?: string) {
    const targetLocale = localeOverride ?? get(locale)
    const formatter = new Intl.NumberFormat(targetLocale)
    const characters = 'characters' /* @wc-include */
    return `${formatter.format(count)}/${formatter.format(limit)} ${characters}`
}
