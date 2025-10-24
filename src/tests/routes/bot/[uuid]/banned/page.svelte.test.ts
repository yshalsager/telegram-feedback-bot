import {render, screen, waitFor} from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import {beforeEach, describe, expect, it, vi} from 'vitest'
import BannedPage from '~/routes/bot/[uuid]/banned/+page.svelte'

const gotoMock = vi.hoisted(() => vi.fn())
const resolveMock = vi.hoisted(() => vi.fn((path: string) => path))
const showNotificationMock = vi.hoisted(() => vi.fn())
const listBannedUsersMock = vi.hoisted(() => vi.fn(async () => [] as unknown))
const banUserMock = vi.hoisted(() => vi.fn(async () => ({})))
const unbanUserMock = vi.hoisted(() => vi.fn(async () => ({})))
const bot = vi.hoisted(() => ({
    uuid: 'bot-uuid',
    telegram_id: 999,
    name: 'Feedback Bot',
    username: 'feedback_bot',
    owner_username: 'owner',
    owner_telegram_id: 1,
    start_message: 'start',
    feedback_received_message: 'received',
    enabled: true,
    forward_chat_id: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z'
}))

type PageState = {
    data: unknown
    error: unknown
    form: unknown
    params: Record<string, string>
    route: {id: string}
    state: Record<string, unknown>
    status: number
    url: URL
}

function createPageState(): PageState {
    return {
        data: {
            bot,
            bannedUsers: [],
            bannedError: null,
            errorMessage: null
        },
        error: null,
        form: null,
        params: {uuid: bot.uuid},
        route: {id: ''},
        state: {},
        status: 200,
        url: new URL('https://example.test/bot/bot-uuid/banned')
    }
}

const pageState = vi.hoisted(() => createPageState())

vi.mock('$app/state', () => ({
    page: pageState,
    navigating: {to: null, from: null, type: null, delta: null},
    updated: {current: false, check: vi.fn()}
}))

vi.mock('$app/navigation', () => ({
    goto: gotoMock
}))

vi.mock('$app/paths', () => ({
    resolve: resolveMock
}))

vi.mock('~/lib/telegram.js', () => ({
    showNotification: showNotificationMock
}))

vi.mock('$lib/api.js', () => ({
    list_banned_users: (...args: unknown[]) => listBannedUsersMock(...args),
    ban_user: (...args: unknown[]) => banUserMock(...args),
    unban_user: (...args: unknown[]) => unbanUserMock(...args)
}))

describe('bot banned users page', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        Object.assign(pageState, createPageState())
        listBannedUsersMock.mockResolvedValue([])
    })

    it('renders existing banned users', () => {
        const existing = {
            user_telegram_id: 123456,
            created_at: '2025-01-01T12:00:00Z',
            reason: 'spam'
        }
        pageState.data = {
            bot,
            bannedUsers: [existing],
            bannedError: null,
            errorMessage: null
        }

        render(BannedPage)

        expect(screen.getByText(existing.user_telegram_id.toLocaleString())).toBeInTheDocument()
        expect(screen.getByText(/Reason: spam/)).toBeInTheDocument()
    })

    it('bans a user and refreshes the list', async () => {
        listBannedUsersMock.mockResolvedValueOnce([
            {
                user_telegram_id: 222222,
                created_at: '2025-01-02T00:00:00Z',
                reason: 'abuse'
            }
        ])
        banUserMock.mockResolvedValue({status: 'success', message: 'User banned'})

        const user = userEvent.setup()
        render(BannedPage)

        await user.type(screen.getByLabelText('Telegram user ID'), '222222')
        await user.type(screen.getByLabelText('Ban reason'), 'abuse')
        await user.click(screen.getByRole('button', {name: 'Ban user'}))

        await waitFor(() => {
            expect(banUserMock).toHaveBeenCalledWith(bot.uuid, 222222, 'abuse')
        })
        await waitFor(() => {
            expect(listBannedUsersMock).toHaveBeenCalledWith(bot.uuid)
        })

        expect(showNotificationMock).toHaveBeenCalledWith('', '✅ User banned')
        expect(await screen.findByText('222,222')).toBeInTheDocument()
        expect(await screen.findByText(/Reason: abuse/)).toBeInTheDocument()
    })

    it('shows an error when banning fails', async () => {
        banUserMock.mockResolvedValue({status: 'error', message: 'Invalid'})

        const user = userEvent.setup()
        render(BannedPage)

        await user.type(screen.getByLabelText('Telegram user ID'), '123')
        await user.click(screen.getByRole('button', {name: 'Ban user'}))

        await waitFor(() => {
            expect(banUserMock).toHaveBeenCalledWith(bot.uuid, 123, '')
        })

        expect(showNotificationMock).toHaveBeenCalledWith('', '❗ Invalid')
        expect(listBannedUsersMock).not.toHaveBeenCalled()
    })

    it('unbans a user and refreshes the list', async () => {
        pageState.data = {
            bot,
            bannedUsers: [
                {
                    user_telegram_id: 333333,
                    created_at: '2025-01-03T00:00:00Z',
                    reason: null
                }
            ],
            bannedError: null,
            errorMessage: null
        }

        unbanUserMock.mockResolvedValue({status: 'success', message: 'User removed', removed: true})
        listBannedUsersMock.mockResolvedValueOnce([])

        const user = userEvent.setup()
        render(BannedPage)

        await user.click(screen.getByRole('button', {name: 'Unban'}))

        await waitFor(() => {
            expect(unbanUserMock).toHaveBeenCalledWith(bot.uuid, 333333)
        })
        await waitFor(() => {
            expect(listBannedUsersMock).toHaveBeenCalledWith(bot.uuid)
        })

        expect(showNotificationMock).toHaveBeenCalledWith('', '✅ User removed')
        await waitFor(() => {
            expect(screen.queryByText('333,333')).not.toBeInTheDocument()
        })
    })
})
