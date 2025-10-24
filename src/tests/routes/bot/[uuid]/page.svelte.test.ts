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
    communication_mode: 'standard' | 'private' | 'anonymous'
    allow_photo_messages: boolean
    allow_video_messages: boolean
    allow_voice_messages: boolean
    allow_document_messages: boolean
    allow_sticker_messages: boolean
    antiflood_enabled: boolean
    antiflood_seconds: number
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
    communication_mode: 'standard',
    allow_photo_messages: true,
    allow_video_messages: true,
    allow_voice_messages: true,
    allow_document_messages: true,
    allow_sticker_messages: true,
    antiflood_enabled: false,
    antiflood_seconds: 60,
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
            feedback_received_message: 'Updated reply',
            communication_mode: 'standard'
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
                communication_mode: updatedBot.communication_mode,
                allow_photo_messages: updatedBot.allow_photo_messages,
                allow_video_messages: updatedBot.allow_video_messages,
                allow_voice_messages: updatedBot.allow_voice_messages,
                allow_document_messages: updatedBot.allow_document_messages,
                allow_sticker_messages: updatedBot.allow_sticker_messages,
                antiflood_enabled: updatedBot.antiflood_enabled,
                antiflood_seconds: updatedBot.antiflood_seconds
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
            username: 'new_feedback_bot',
            communication_mode: 'standard'
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
                communication_mode: baseBot.communication_mode,
                allow_photo_messages: baseBot.allow_photo_messages,
                allow_video_messages: baseBot.allow_video_messages,
                allow_voice_messages: baseBot.allow_voice_messages,
                allow_document_messages: baseBot.allow_document_messages,
                allow_sticker_messages: baseBot.allow_sticker_messages,
                antiflood_seconds: baseBot.antiflood_seconds,
                antiflood_enabled: baseBot.antiflood_enabled,
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
                communication_mode: baseBot.communication_mode,
                allow_photo_messages: baseBot.allow_photo_messages,
                allow_video_messages: baseBot.allow_video_messages,
                allow_voice_messages: false,
                allow_document_messages: baseBot.allow_document_messages,
                allow_sticker_messages: baseBot.allow_sticker_messages,
                antiflood_seconds: baseBot.antiflood_seconds,
                antiflood_enabled: baseBot.antiflood_enabled
            })
        })

        expect(mapBotResponseMock).toHaveBeenCalledWith({uuid: baseBot.uuid}, baseBot.uuid)
        expect(showNotificationMock).toHaveBeenCalledWith('', '✅ Bot updated successfully')
    })

    it('updates communication mode when selection changes', async () => {
        setPageState({
            params: {uuid: baseBot.uuid},
            data: {bot: baseBot, errorMessage: null}
        })

        const modeBot: Bot = {
            ...baseBot,
            communication_mode: 'private'
        }

        updateBotMock.mockResolvedValue({uuid: baseBot.uuid})
        mapBotResponseMock.mockReturnValue(modeBot)

        const user = userEvent.setup()
        render(BotPage)

        const privateOption = screen.getByLabelText(/Private/, {
            selector: 'input[type="radio"]'
        }) as HTMLInputElement
        expect(privateOption).toBeInTheDocument()
        await user.click(privateOption)

        const saveButton = screen.getByRole('button', {name: 'Save'})
        await user.click(saveButton)

        await waitFor(() => {
            expect(updateBotMock).toHaveBeenCalledWith(baseBot.uuid, {
                start_message: baseBot.start_message,
                feedback_received_message: baseBot.feedback_received_message,
                enabled: baseBot.enabled,
                communication_mode: 'private',
                allow_photo_messages: baseBot.allow_photo_messages,
                allow_video_messages: baseBot.allow_video_messages,
                allow_voice_messages: baseBot.allow_voice_messages,
                allow_document_messages: baseBot.allow_document_messages,
                allow_sticker_messages: baseBot.allow_sticker_messages,
                antiflood_seconds: baseBot.antiflood_seconds,
                antiflood_enabled: baseBot.antiflood_enabled
            })
        })

        expect(mapBotResponseMock).toHaveBeenCalledWith({uuid: baseBot.uuid}, baseBot.uuid)
    })

    it('updates antiflood setting when toggled', async () => {
        setPageState({
            params: {uuid: baseBot.uuid},
            data: {bot: baseBot, errorMessage: null}
        })

        const antifloodBot: Bot = {
            ...baseBot,
            antiflood_enabled: true
        }

        updateBotMock.mockResolvedValue({uuid: baseBot.uuid})
        mapBotResponseMock.mockReturnValue(antifloodBot)

        const user = userEvent.setup()
        render(BotPage)

        const antifloodToggle = screen.getByRole('switch', {name: 'Anti-flood'})
        await user.click(antifloodToggle)

        const saveButton = screen.getByRole('button', {name: 'Save'})
        await user.click(saveButton)

        await waitFor(() => {
            expect(updateBotMock).toHaveBeenCalledWith(baseBot.uuid, {
                start_message: baseBot.start_message,
                feedback_received_message: baseBot.feedback_received_message,
                enabled: baseBot.enabled,
                communication_mode: baseBot.communication_mode,
                allow_photo_messages: baseBot.allow_photo_messages,
                allow_video_messages: baseBot.allow_video_messages,
                allow_voice_messages: baseBot.allow_voice_messages,
                allow_document_messages: baseBot.allow_document_messages,
                allow_sticker_messages: baseBot.allow_sticker_messages,
                antiflood_seconds: baseBot.antiflood_seconds,
                antiflood_enabled: true
            })
        })

        expect(mapBotResponseMock).toHaveBeenCalledWith({uuid: baseBot.uuid}, baseBot.uuid)
        expect(showNotificationMock).toHaveBeenCalledWith('', '✅ Bot updated successfully')
    })

    it('updates antiflood cooldown value', async () => {
        setPageState({
            params: {uuid: baseBot.uuid},
            data: {bot: baseBot, errorMessage: null}
        })

        const antifloodBot: Bot = {
            ...baseBot,
            antiflood_enabled: true,
            antiflood_seconds: 90
        }

        updateBotMock.mockResolvedValue({uuid: baseBot.uuid})
        mapBotResponseMock.mockReturnValue(antifloodBot)

        const user = userEvent.setup()
        render(BotPage)

        const antifloodToggle = screen.getByRole('switch', {name: 'Anti-flood'})
        await user.click(antifloodToggle)

        const cooldownInput = screen.getByLabelText('Anti-flood wait (seconds)') as HTMLInputElement
        expect(cooldownInput).toBeInstanceOf(HTMLInputElement)
        await user.clear(cooldownInput)
        await user.type(cooldownInput, '90')

        const saveButton = screen.getByRole('button', {name: 'Save'})
        await user.click(saveButton)

        await waitFor(() => {
            expect(updateBotMock).toHaveBeenCalledWith(baseBot.uuid, {
                start_message: baseBot.start_message,
                feedback_received_message: baseBot.feedback_received_message,
                enabled: baseBot.enabled,
                communication_mode: baseBot.communication_mode,
                allow_photo_messages: baseBot.allow_photo_messages,
                allow_video_messages: baseBot.allow_video_messages,
                allow_voice_messages: baseBot.allow_voice_messages,
                allow_document_messages: baseBot.allow_document_messages,
                allow_sticker_messages: baseBot.allow_sticker_messages,
                antiflood_enabled: true,
                antiflood_seconds: 90
            })
        })

        expect(mapBotResponseMock).toHaveBeenCalledWith({uuid: baseBot.uuid}, baseBot.uuid)
        expect(showNotificationMock).toHaveBeenCalledWith('', '✅ Bot updated successfully')
    })

    it('allows switching away from anonymous mode', async () => {
        const anonymousBot: Bot = {
            ...baseBot,
            communication_mode: 'anonymous'
        }

        setPageState({
            params: {uuid: anonymousBot.uuid},
            data: {bot: anonymousBot, errorMessage: null}
        })

        updateBotMock.mockResolvedValue({uuid: anonymousBot.uuid})
        mapBotResponseMock.mockReturnValue({...anonymousBot, communication_mode: 'standard'})

        const user = userEvent.setup()
        render(BotPage)

        const standardOption = screen.getByLabelText(/Standard/, {
            selector: 'input[type="radio"]'
        }) as HTMLInputElement
        const saveButton = screen.getByRole('button', {name: 'Save'})

        expect(standardOption).not.toBeDisabled()
        await user.click(standardOption)
        await user.click(saveButton)

        await waitFor(() => {
            expect(updateBotMock).toHaveBeenCalledWith(anonymousBot.uuid, {
                start_message: anonymousBot.start_message,
                feedback_received_message: anonymousBot.feedback_received_message,
                enabled: anonymousBot.enabled,
                communication_mode: 'standard',
                allow_photo_messages: anonymousBot.allow_photo_messages,
                allow_video_messages: anonymousBot.allow_video_messages,
                allow_voice_messages: anonymousBot.allow_voice_messages,
                allow_document_messages: anonymousBot.allow_document_messages,
                allow_sticker_messages: anonymousBot.allow_sticker_messages,
                antiflood_seconds: anonymousBot.antiflood_seconds,
                antiflood_enabled: anonymousBot.antiflood_enabled
            })
        })
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
