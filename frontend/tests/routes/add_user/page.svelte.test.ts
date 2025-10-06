import {render, screen} from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import {beforeEach, describe, expect, it, vi} from 'vitest'
import AddUserPage from '~/routes/add_user/+page.svelte'

const gotoMock = vi.hoisted(() => vi.fn())
const onMock = vi.hoisted(() => vi.fn(() => vi.fn()))
const showNotificationMock = vi.hoisted(() => vi.fn())
const addUserMock = vi.hoisted(() => vi.fn(async () => ({})))

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

vi.mock('$app/navigation', () => ({
    goto: gotoMock
}))

vi.mock('$app/paths', () => ({
    resolve: (path: string) => path
}))

vi.mock('@telegram-apps/sdk-svelte', () => ({
    on: onMock
}))

vi.mock('~/lib/telegram.js', () => ({
    showNotification: showNotificationMock
}))

vi.mock('$lib/api.js', () => ({
    add_user: (...args: unknown[]) => addUserMock(...args)
}))

vi.mock('~/lib/i18n', () => ({
    locale: i18nMock.localeStore,
    locales: ['en', 'ar'],
    availableLocales: i18nMock.availableLocales,
    formatCharacterCount: i18nMock.formatCharacterCount,
    applyLocale: i18nMock.applyLocale
}))

describe('add_user +page.svelte', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        addUserMock.mockReset()
        addUserMock.mockResolvedValue({
            status: 'success',
            user: {username: 'newuser', telegram_id: 42}
        })
        i18nMock.reset()
    })

    it('shows validation error when user id is missing', async () => {
        const user = userEvent.setup()
        render(AddUserPage)

        const idInput = screen.getByLabelText('User ID') as HTMLInputElement
        const saveButton = screen.getByRole('button', {name: 'Save'})

        await user.type(idInput, 'abc')

        expect(saveButton).toBeDisabled()
        expect(screen.getByRole('alert')).toHaveTextContent(
            'Enter a valid numeric Telegram user ID.'
        )
    })

    it('submits new user details and shows notification', async () => {
        const user = userEvent.setup()
        render(AddUserPage)

        const idInput = screen.getByLabelText('User ID') as HTMLInputElement
        const usernameInput = screen.getByLabelText('Username') as HTMLInputElement
        const languageSelect = screen.getByLabelText('Language') as HTMLSelectElement
        const adminSwitch = screen.getByRole('switch', {name: 'Admin access'})
        const saveButton = screen.getByRole('button', {name: 'Save'})

        await user.type(idInput, '123456789')
        await user.clear(usernameInput)
        await user.type(usernameInput, '@newuser')
        await user.selectOptions(languageSelect, 'ar')
        await user.click(adminSwitch)

        expect(saveButton).not.toBeDisabled()

        await user.click(saveButton)

        await expect(addUserMock).toHaveBeenCalledWith(123456789, 'newuser', 'ar', true, true)
        expect(showNotificationMock).toHaveBeenCalledWith(
            '',
            'Successfully updated access for @newuser.',
            [{id: 'user_successfully_added_close', type: 'close'}]
        )

        expect(idInput.value).toBe('')
        expect(usernameInput.value).toBe('')
        expect(languageSelect.value).toBe('en')
        expect(adminSwitch).toHaveAttribute('aria-checked', 'false')
    })
})
