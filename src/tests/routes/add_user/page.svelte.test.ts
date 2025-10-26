import {render, screen} from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import {beforeEach, describe, expect, it, vi} from 'vitest'
import AddUserPage from '~/routes/app/add_user/+page.svelte'

vi.mock('~/lib/i18n', () => {
    const localeStore = {
        subscribe: (fn: (value: string) => void) => {
            fn('en')
            return () => {}
        },
        set: vi.fn()
    }
    const availableLocales = {
        subscribe: (fn: (value: Array<{locale: string; name: string}>) => void) => {
            fn([
                {locale: 'en', name: 'English'},
                {locale: 'ar', name: 'Arabic'}
            ])
            return () => {}
        }
    }
    return {
        locale: localeStore,
        locales: ['en', 'ar'],
        availableLocales,
        formatNumber: (value: number) => value.toString(),
        formatCharacterCount: (value: number, limit = 4096) => `${value}/${limit}`,
        applyLocale: vi.fn(),
        initLocale: vi.fn(async () => 'en')
    }
})

const gotoMock = vi.hoisted(() => vi.fn())
const onMock = vi.hoisted(() => vi.fn(() => vi.fn()))
const showNotificationMock = vi.hoisted(() => vi.fn())
const addUserMock = vi.hoisted(() => vi.fn(async () => ({})))

vi.mock('$app/navigation', () => ({
    goto: gotoMock
}))

vi.mock('$app/paths', () => ({
    resolve: (path: string) => path
}))

vi.mock('@tma.js/sdk-svelte', () => ({
    on: onMock
}))

vi.mock('~/lib/telegram.js', () => ({
    showNotification: showNotificationMock
}))

vi.mock('$lib/api.js', () => ({
    add_user: (...args: unknown[]) => addUserMock(...args)
}))

describe('add_user +page.svelte', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        addUserMock.mockReset()
        addUserMock.mockResolvedValue({
            status: 'success',
            user: {username: 'newuser', telegram_id: 42}
        })
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
