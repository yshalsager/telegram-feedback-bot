import {render, screen, waitFor} from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import {beforeEach, describe, expect, it, vi} from 'vitest'
import BotPage from '~/routes/bot/[uuid]/+page.svelte'

const gotoMock = vi.hoisted(() => vi.fn())
const onMock = vi.hoisted(() => vi.fn(() => vi.fn()))
const showNotificationMock = vi.hoisted(() => vi.fn())
const updateBotMock = vi.hoisted(() => vi.fn())
const deleteBotMock = vi.hoisted(() => vi.fn())
const mapBotResponseMock = vi.hoisted(() => vi.fn())

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

const setPageState = (overrides: Partial<ReturnType<typeof createPageState>>) => {
    Object.assign(pageState, overrides)
}

const resetPageState = () => {
    Object.assign(pageState, createPageState())
}

vi.mock('$app/state', () => ({
    page: pageState,
    navigating: {to: null, from: null, type: null, delta: null},
    updated: {current: false, check: vi.fn()}
}))

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
    update_bot: (...args: unknown[]) => updateBotMock(...args),
    delete_bot: (...args: unknown[]) => deleteBotMock(...args)
}))

vi.mock('$lib/mappers/bot', () => ({
    mapBotResponse: (...args: unknown[]) => mapBotResponseMock(...args)
}))

vi.mock('~/lib/i18n', () => ({
    formatCharacterCount: (value: number, limit = 4096) => `${value}/${limit}`
}))

type Bot = {
    uuid: string
    telegram_id: number
    name: string
    username: string
    owner_username: string
    owner_telegram_id: number
    start_message: string
    feedback_received_message: string
    confirmations_on: boolean
    enabled: boolean
    forward_chat_id: number | null
    created_at: string
    updated_at: string
}

const baseBot: Bot = {
    uuid: 'bot-uuid',
    telegram_id: 123,
    name: 'Feedback Bot',
    username: 'feedback_bot',
    owner_username: 'owner',
    owner_telegram_id: 456,
    start_message: 'Welcome!',
    feedback_received_message: 'Thanks for sharing',
    confirmations_on: true,
    enabled: true,
    forward_chat_id: null,
    created_at: new Date('2024-01-01').toISOString(),
    updated_at: new Date('2024-01-02').toISOString()
}

describe('+page.svelte', () => {
    beforeEach(() => {
        resetPageState()
        vi.clearAllMocks()
    })

    it('notifies and shows error message when bot data is missing', () => {
        setPageState({
            params: {uuid: 'missing-bot'},
            data: {bot: null, errorMessage: 'Failed to load bot'}
        })

        render(BotPage)

        expect(screen.getByText('Failed to load bot', {exact: false})).toBeInTheDocument()
        expect(showNotificationMock).toHaveBeenCalledWith('', '❗ Failed to load bot')
    })

    it('submits updates and shows success notification', async () => {
        setPageState({
            params: {uuid: baseBot.uuid},
            data: {bot: baseBot, errorMessage: null}
        })

        const updatedBot: Bot = {
            ...baseBot,
            start_message: 'New welcome message',
            feedback_received_message: 'Updated reply'
        }

        updateBotMock.mockResolvedValue({uuid: baseBot.uuid})
        mapBotResponseMock.mockReturnValue(updatedBot)

        const user = userEvent.setup()
        render(BotPage)

        const startMessage = document.getElementById('start-message') as HTMLTextAreaElement
        const feedbackMessage = document.getElementById('feedback-message') as HTMLTextAreaElement

        expect(startMessage).toBeInstanceOf(HTMLTextAreaElement)
        expect(feedbackMessage).toBeInstanceOf(HTMLTextAreaElement)

        const [saveButton] = Array.from(
            document.querySelectorAll<HTMLButtonElement>('button[data-slot="button"]')
        )
        expect(saveButton).toBeInstanceOf(HTMLButtonElement)

        await user.clear(startMessage)
        await user.type(startMessage, 'New welcome message')
        await user.clear(feedbackMessage)
        await user.type(feedbackMessage, 'Updated reply')

        await user.click(saveButton as HTMLButtonElement)

        await waitFor(() => {
            expect(updateBotMock).toHaveBeenCalledWith(baseBot.uuid, {
                enable_confirmations: updatedBot.confirmations_on,
                start_message: 'New welcome message',
                feedback_received_message: 'Updated reply',
                enabled: updatedBot.enabled
            })
        })

        expect(mapBotResponseMock).toHaveBeenCalledWith({uuid: baseBot.uuid}, baseBot.uuid)
        expect(showNotificationMock).toHaveBeenCalledWith('', '✅ Bot updated successfully')
    })

    it('asks for confirmation before deleting a bot', async () => {
        setPageState({
            params: {uuid: baseBot.uuid},
            data: {bot: baseBot, errorMessage: null}
        })

        deleteBotMock.mockResolvedValue({status: 'success'})
        const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

        const user = userEvent.setup()
        render(BotPage)

        const buttons = Array.from(
            document.querySelectorAll<HTMLButtonElement>('button[data-slot="button"]')
        )
        const deleteButton =
            buttons[1] ?? buttons.find(button => button.textContent?.includes('Delete'))

        expect(deleteButton).toBeInstanceOf(HTMLButtonElement)

        await user.click(deleteButton as HTMLButtonElement)

        expect(confirmSpy).toHaveBeenCalledTimes(1)
        await waitFor(() => {
            expect(deleteBotMock).toHaveBeenCalledWith(baseBot.uuid)
        })
        expect(showNotificationMock).toHaveBeenCalledWith('', '✅ Bot deleted successfully', [
            {id: 'bot_deleted_success_close', type: 'close'}
        ])
    })

    it('registers Telegram popup closed handler once', () => {
        setPageState({
            params: {uuid: baseBot.uuid},
            data: {bot: baseBot, errorMessage: null}
        })

        render(BotPage)

        expect(onMock).toHaveBeenCalledWith('popup_closed', expect.any(Function))
        expect(onMock).toHaveBeenCalledTimes(1)
    })
})
