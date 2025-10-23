import type {Readable, Writable} from 'svelte/store'

type LocaleInfo = {locale: string; name: string}

export type I18nMock = {
    localeStore: Writable<string>
    availableLocales: Readable<LocaleInfo[]>
    formatCharacterCount: (count: number, limit?: number) => string
    applyLocale: (code: string) => Promise<void>
    reset: () => void
}

let currentMock: I18nMock | null = null

function createMock(): I18nMock {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const {derived, writable} = require('svelte/store') as typeof import('svelte/store')

    const locales = ['en', 'ar'] as const
    const initialLocale = locales[0] ?? 'en'

    const localeStore = writable(initialLocale)
    const availableLocales = derived(localeStore, () =>
        locales.map(locale => ({
            locale,
            name: locale === 'en' ? 'English' : locale === 'ar' ? 'Arabic' : locale
        }))
    )

    const formatCharacterCount = (count: number, limit = 4096) => `${count}/${limit}`
    const applyLocale = async (code: string) => {
        localeStore.set(code)
    }

    return {
        localeStore,
        availableLocales,
        formatCharacterCount,
        applyLocale,
        reset() {
            localeStore.set(initialLocale)
        }
    }
}

export function createI18nMockModule() {
    const mock = createMock()
    currentMock = mock
    return {
        locale: mock.localeStore,
        locales: ['en', 'ar'],
        availableLocales: mock.availableLocales,
        formatCharacterCount: mock.formatCharacterCount,
        applyLocale: mock.applyLocale
    }
}

export function getI18nMock() {
    if (!currentMock) {
        throw new Error('i18n mock has not been initialised')
    }
    return currentMock
}
