import {render, screen, waitFor} from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import {beforeEach, describe, expect, it, vi} from 'vitest'
import SettingsPage from '~/routes/settings/+page.svelte'

const setLanguageMock = vi.hoisted(() => vi.fn(async () => true))
const showNotificationMock = vi.hoisted(() => vi.fn())

const i18nMock = vi.hoisted(() => {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const {derived, writable} = require('svelte/store')
    const localeStore = writable('en')
    const availableLocales = derived(localeStore, () => [
        {locale: 'en', name: 'English'},
        {locale: 'ar', name: 'Arabic'}
    ])
    const formatCharacterCount = vi.fn((count: number, limit = 4096) => `${count}/${limit}`)
    const applyLocale = vi.fn(async (code: string) => {
        localeStore.set(code)
    })
    return {
        localeStore,
        availableLocales,
        formatCharacterCount,
        applyLocale,
        reset() {
            localeStore.set('en')
        }
    }
})

const sessionMock = vi.hoisted(() => {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const {writable} = require('svelte/store')
    const initial = () => ({
        data: {
            user: {
                first_name: 'Jane',
                last_name: 'Doe',
                username: 'janed',
                id: 42,
                language_code: 'en',
                photo_url: null
            }
        }
    })
    const store = writable(initial())
    const {subscribe, set, update} = store
    const updateSpy = vi.fn((updater: (value: unknown) => unknown) => update(updater))
    return {
        store: {subscribe, set, update: updateSpy},
        updateSpy,
        reset() {
            set(initial())
        }
    }
})

vi.mock('$lib/api.js', () => ({
    set_language: (...args: unknown[]) => setLanguageMock(...args)
}))

vi.mock('~/lib/telegram.js', () => ({
    showNotification: showNotificationMock
}))

vi.mock('~/lib/stores.svelte.js', () => ({
    session: sessionMock.store
}))

vi.mock('~/lib/i18n', () => ({
    locale: i18nMock.localeStore,
    availableLocales: i18nMock.availableLocales,
    locales: ['en', 'ar'],
    applyLocale: i18nMock.applyLocale,
    formatCharacterCount: i18nMock.formatCharacterCount
}))

describe('settings +page.svelte', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        i18nMock.reset()
        sessionMock.reset()
        setLanguageMock.mockResolvedValue(true)
    })

    it('renders current user information from session store', () => {
        render(SettingsPage)

        expect(screen.getByText('Jane Doe')).toBeInTheDocument()
        expect(screen.getByText('@janed')).toBeInTheDocument()
        expect(screen.getByText('Language', {selector: 'p'})).toBeInTheDocument()
        expect(screen.getByText('English')).toBeInTheDocument()
        expect(screen.getByText('en')).toBeInTheDocument()
    })

    it('updates language when a different locale is selected', async () => {
        const user = userEvent.setup()
        render(SettingsPage)

        await user.click(screen.getByRole('button', {name: 'Arabic'}))

        await waitFor(() => {
            expect(setLanguageMock).toHaveBeenCalledWith('ar')
        })
        expect(i18nMock.applyLocale).toHaveBeenCalledWith('ar')
        expect(sessionMock.updateSpy).toHaveBeenCalled()
    })

    it('shows notification when language change fails', async () => {
        setLanguageMock.mockResolvedValue(false)
        const user = userEvent.setup()
        render(SettingsPage)

        await user.click(screen.getByRole('button', {name: 'Arabic'}))

        await waitFor(() => {
            expect(showNotificationMock).toHaveBeenCalledWith(
                'Failed to set language',
                'Please try again later',
                [{id: 'language_error_close', type: 'close'}]
            )
        })
        expect(i18nMock.applyLocale).not.toHaveBeenCalled()
    })
})
