import {render, screen} from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import {beforeEach, describe, expect, it, vi} from 'vitest'
import AddBotPage from '~/routes/add_bot/+page.svelte'

const gotoMock = vi.hoisted(() => vi.fn())
const onMock = vi.hoisted(() => vi.fn(() => vi.fn()))
const showNotificationMock = vi.hoisted(() => vi.fn())
const addBotMock = vi.hoisted(() => vi.fn(async () => ({})))

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
    add_bot: (...args: unknown[]) => addBotMock(...args)
}))

vi.mock('~/lib/i18n', () => ({
    locale: i18nMock.localeStore,
    locales: ['en', 'ar'],
    availableLocales: i18nMock.availableLocales,
    formatCharacterCount: i18nMock.formatCharacterCount,
    applyLocale: i18nMock.applyLocale
}))

describe('add_bot +page.svelte', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        addBotMock.mockReset()
        addBotMock.mockResolvedValue({status: 'success', bot: {username: 'new_bot'}})
        i18nMock.reset()
    })

    it('validates bot token format and keeps save disabled when invalid', async () => {
        const user = userEvent.setup()
        render(AddBotPage)

        const tokenInput = screen.getByLabelText('Bot token') as HTMLInputElement
        const saveButton = screen.getByRole('button', {name: 'Save'})

        await user.type(tokenInput, 'invalid')

        expect(saveButton).toBeDisabled()
        expect(screen.getByRole('alert')).toHaveTextContent('Bot token must be in format')
        expect(addBotMock).not.toHaveBeenCalled()
    })

    it('submits form and shows success notification for valid input', async () => {
        const user = userEvent.setup()
        render(AddBotPage)

        const validToken = `12345678:${'A'.repeat(35)}`
        const tokenInput = screen.getByLabelText('Bot token') as HTMLInputElement
        const saveButton = screen.getByRole('button', {name: 'Save'})

        await user.type(tokenInput, validToken)
        expect(saveButton).not.toBeDisabled()

        await user.click(saveButton)

        await expect(addBotMock).toHaveBeenCalledWith(
            validToken,
            true,
            expect.stringContaining('Welcome'),
            expect.stringContaining('Thank you')
        )
        expect(showNotificationMock).toHaveBeenCalledWith('', expect.stringContaining('@new_bot'), [
            {id: 'bot_successfully_added_close', type: 'close'}
        ])
    })
})
