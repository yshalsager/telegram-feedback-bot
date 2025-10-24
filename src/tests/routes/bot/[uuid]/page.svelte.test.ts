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
const rotatedToken = '23456789:bcdefghijklmnopqrstuvwxyzABCDE12345'

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
    enabled: boolean
    allow_photo_messages: boolean
    allow_video_messages: boolean
    allow_voice_messages: boolean
    allow_document_messages: boolean
    allow_sticker_messages: boolean
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
    enabled: true,
    allow_photo_messages: true,
    allow_video_messages: true,
    allow_voice_messages: true,
    allow_document_messages: true,
    allow_sticker_messages: true,
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

        const saveButton = screen.getByRole('button', {name: 'Save'})
        expect(saveButton).toBeInstanceOf(HTMLButtonElement)

        await user.clear(startMessage)
        await user.type(startMessage, 'New welcome message')
        await user.clear(feedbackMessage)
        await user.type(feedbackMessage, 'Updated reply')

        await user.click(saveButton)

        await waitFor(() => {
            expect(updateBotMock).toHaveBeenCalledWith(baseBot.uuid, {
                start_message: 'New welcome message',
                feedback_received_message: 'Updated reply',
                enabled: updatedBot.enabled,
                allow_photo_messages: updatedBot.allow_photo_messages,
                allow_video_messages: updatedBot.allow_video_messages,
                allow_voice_messages: updatedBot.allow_voice_messages,
                allow_document_messages: updatedBot.allow_document_messages,
                allow_sticker_messages: updatedBot.allow_sticker_messages
            })
        })

        expect(mapBotResponseMock).toHaveBeenCalledWith({uuid: baseBot.uuid}, baseBot.uuid)
        expect(showNotificationMock).toHaveBeenCalledWith('', '✅ Bot updated successfully')
    })

    it('rotates token when a new value is provided', async () => {
        setPageState({
            params: {uuid: baseBot.uuid},
            data: {bot: baseBot, errorMessage: null}
        })

        const rotatedBot: Bot = {
            ...baseBot,
            name: 'New Bot Name',
            username: 'new_feedback_bot'
        }

        updateBotMock.mockResolvedValue({uuid: baseBot.uuid})
        mapBotResponseMock.mockReturnValue(rotatedBot)

        const user = userEvent.setup()
        render(BotPage)

        const tokenInput = screen.getByLabelText('Bot token') as HTMLInputElement
        await user.type(tokenInput, rotatedToken)

        const saveButton = screen.getByRole('button', {name: 'Save'})
        await user.click(saveButton)

        await waitFor(() => {
            expect(updateBotMock).toHaveBeenCalledWith(baseBot.uuid, {
                start_message: baseBot.start_message,
                feedback_received_message: baseBot.feedback_received_message,
                enabled: baseBot.enabled,
                allow_photo_messages: baseBot.allow_photo_messages,
                allow_video_messages: baseBot.allow_video_messages,
                allow_voice_messages: baseBot.allow_voice_messages,
                allow_document_messages: baseBot.allow_document_messages,
                allow_sticker_messages: baseBot.allow_sticker_messages,
                bot_token: rotatedToken
            })
        })

        expect(mapBotResponseMock).toHaveBeenCalledWith({uuid: baseBot.uuid}, baseBot.uuid)
        expect(tokenInput.value).toBe('')
        expect(showNotificationMock).toHaveBeenCalledWith('', '✅ Bot updated successfully')
    })

    it('updates media permissions when toggles change', async () => {
        setPageState({
            params: {uuid: baseBot.uuid},
            data: {bot: baseBot, errorMessage: null}
        })

        const toggledBot: Bot = {
            ...baseBot,
            allow_voice_messages: false
        }

        updateBotMock.mockResolvedValue({uuid: baseBot.uuid})
        mapBotResponseMock.mockReturnValue(toggledBot)

        const user = userEvent.setup()
        render(BotPage)

        const voiceToggle = screen.getByRole('switch', {name: 'Voice messages'})
        await user.click(voiceToggle)

        const saveButton = screen.getByRole('button', {name: 'Save'})
        await user.click(saveButton)

        await waitFor(() => {
            expect(updateBotMock).toHaveBeenCalledWith(baseBot.uuid, {
                start_message: baseBot.start_message,
                feedback_received_message: baseBot.feedback_received_message,
                enabled: baseBot.enabled,
                allow_photo_messages: baseBot.allow_photo_messages,
                allow_video_messages: baseBot.allow_video_messages,
                allow_voice_messages: false,
                allow_document_messages: baseBot.allow_document_messages,
                allow_sticker_messages: baseBot.allow_sticker_messages
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

        const deleteButton = screen.getByRole('button', {name: /Delete bot/})

        expect(deleteButton).toBeInstanceOf(HTMLButtonElement)

        await user.click(deleteButton)

        expect(confirmSpy).toHaveBeenCalledTimes(1)
        await waitFor(() => {
            expect(deleteBotMock).toHaveBeenCalledWith(baseBot.uuid)
        })
        expect(showNotificationMock).toHaveBeenCalledWith('', '✅ Bot deleted successfully', [
            {id: 'bot_deleted_success_close', type: 'close'}
        ])
    })

    it('navigates to banned users view', async () => {
        setPageState({
            params: {uuid: baseBot.uuid},
            data: {bot: baseBot, errorMessage: null}
        })

        const user = userEvent.setup()
        render(BotPage)

        const manageBannedButton = screen.getByRole('button', {name: 'Manage banned users'})
        await user.click(manageBannedButton)

        expect(gotoMock).toHaveBeenCalledWith(`/bot/${baseBot.uuid}/banned`)
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
