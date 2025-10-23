import {error} from '@sveltejs/kit'
import {list_banned_users as fetch_banned_users, get_bot} from '$lib/api.js'
import {mapBotResponse} from '$lib/mappers/bot'
import type {BannedUser} from '$lib/types.ts'
import type {PageLoad} from './$types'

type BannedListResponse = {
    status?: string
    message?: unknown
}

function normalize_banned_users(payload: unknown): BannedUser[] {
    if (!Array.isArray(payload)) return []

    return payload
        .map(entry => {
            if (!entry || typeof entry !== 'object') return null
            const raw = entry as Record<string, unknown>
            const user_id = Number(raw.user_telegram_id)
            if (!Number.isFinite(user_id) || user_id <= 0) return null
            const created_at = typeof raw.created_at === 'string' ? raw.created_at : ''
            const reason_raw = (raw.reason ?? null) as unknown
            const reason = typeof reason_raw === 'string' ? reason_raw : null
            return {
                user_telegram_id: Math.trunc(user_id),
                created_at,
                reason
            }
        })
        .filter(Boolean) as BannedUser[]
}

export const load: PageLoad = async ({params}) => {
    const uuid = params.uuid ?? ''
    if (!uuid) {
        throw error(400, 'Bot identifier is required')
    }

    const bot_response = await get_bot(uuid)

    if (
        bot_response &&
        typeof bot_response === 'object' &&
        'status' in bot_response &&
        bot_response.status === 'error'
    ) {
        const message =
            'message' in bot_response && bot_response.message
                ? String(bot_response.message)
                : 'Bot not found'
        return {
            bot: null,
            bannedUsers: [] as BannedUser[],
            errorMessage: message,
            bannedError: null as string | null
        }
    }

    const bot = mapBotResponse(bot_response as Record<string, unknown>, uuid)

    const banned_response = await fetch_banned_users(uuid)
    let banned_error: string | null = null
    let banned_users: BannedUser[] = []

    if (
        banned_response &&
        typeof banned_response === 'object' &&
        'status' in banned_response &&
        (banned_response as BannedListResponse).status === 'error'
    ) {
        banned_error =
            'message' in banned_response && banned_response.message
                ? String(banned_response.message)
                : 'Unable to load banned users'
    } else {
        banned_users = normalize_banned_users(banned_response)
    }

    return {
        bot,
        bannedUsers: banned_users,
        bannedError: banned_error
    }
}
