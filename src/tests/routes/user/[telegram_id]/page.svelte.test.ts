import {render, screen, waitFor} from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import {beforeEach, describe, expect, it, vi} from 'vitest'
import UserPage from '~/routes/user/[telegram_id]/+page.svelte'

const showNotificationMock = vi.hoisted(() => vi.fn())
const updateUserDetailMock = vi.hoisted(() => vi.fn(async () => ({})))
const mapUserResponseMock = vi.hoisted(() => vi.fn())

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

function createPageState() {
    return {
        data: undefined as unknown,
        error: null as unknown,
        form: null as unknown,
        params: {} as Record<string, string>,
        route: {id: ''},
        state: {},
        status: 200,
        url: new URL('https://example.test/')
    }
}

const pageState = vi.hoisted(() => createPageState())

vi.mock('$app/state', () => ({
    page: pageState,
    navigating: {to: null, from: null, type: null, delta: null},
    updated: {current: false, check: vi.fn()}
}))

vi.mock('~/lib/telegram.js', () => ({
    showNotification: showNotificationMock
}))

vi.mock('$lib/api.js', () => ({
    update_user_detail: (...args: unknown[]) => updateUserDetailMock(...args)
}))

vi.mock('$lib/mappers/user', () => ({
    mapUserResponse: (...args: unknown[]) => mapUserResponseMock(...args)
}))

vi.mock('~/lib/i18n', () => ({
    locale: i18nMock.localeStore,
    locales: ['en', 'ar'],
    availableLocales: i18nMock.availableLocales,
    formatCharacterCount: i18nMock.formatCharacterCount,
    applyLocale: i18nMock.applyLocale
}))

describe('user detail +page.svelte', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        Object.assign(pageState, createPageState())
        i18nMock.reset()
        updateUserDetailMock.mockReset()
        mapUserResponseMock.mockReset()
    })

    it('shows error message when user data is missing', () => {
        pageState.params = {telegram_id: '404'}
        pageState.data = {user: null, errorMessage: 'Failed to load user'}

        render(UserPage)

        expect(screen.getByText('Failed to load user')).toBeInTheDocument()
        expect(showNotificationMock).toHaveBeenCalledWith('', '❗ Failed to load user')
    })

    it('updates user when form is submitted with changes', async () => {
        const existingUser = {
            telegram_id: 123456,
            username: 'existing',
            language_code: 'en',
            is_whitelisted: true,
            is_admin: false
        }

        pageState.params = {telegram_id: String(existingUser.telegram_id)}
        pageState.data = {
            user: existingUser,
            errorMessage: null
        }

        const updatedUser = {
            ...existingUser,
            username: 'newname',
            is_admin: true
        }

        updateUserDetailMock.mockResolvedValue({status: 'success', user: updatedUser})
        mapUserResponseMock.mockReturnValue(updatedUser)

        const user = userEvent.setup()
        render(UserPage)

        const usernameInput = screen.getByLabelText('Username') as HTMLInputElement
        const languageSelect = screen.getByLabelText('Language') as HTMLSelectElement
        const adminSwitch = screen.getByRole('switch', {name: 'Admin access'})
        const saveButton = screen.getByRole('button', {name: 'Save changes'})

        await user.clear(usernameInput)
        await user.type(usernameInput, '@newname')
        await user.selectOptions(languageSelect, 'ar')
        await user.click(adminSwitch)

        expect(saveButton).not.toBeDisabled()

        await user.click(saveButton)

        await waitFor(() => {
            expect(updateUserDetailMock).toHaveBeenCalledWith(existingUser.telegram_id, {
                username: 'newname',
                language_code: 'ar',
                is_admin: true
            })
        })

        expect(mapUserResponseMock).toHaveBeenCalledWith(
            updatedUser,
            existingUser.telegram_id,
            'en'
        )
        expect(showNotificationMock).toHaveBeenCalledWith('', '✅ User updated successfully')
    })
})
