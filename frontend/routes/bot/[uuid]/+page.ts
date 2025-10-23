import {error} from '@sveltejs/kit'
import {get_bot, get_bot_stats} from '$lib/api.js'
import {mapBotResponse} from '$lib/mappers/bot'
import type {BotStats} from '$lib/types.ts'
import type {PageLoad} from './$types'

export const load: PageLoad = async ({params}) => {
    const uuid = params.uuid ?? ''

    if (!uuid) {
        throw error(400, 'Bot identifier is required')
    }

    const response = await get_bot(uuid)

    if (
        response &&
        typeof response === 'object' &&
        'status' in response &&
        response.status === 'error'
    ) {
        const message =
            'message' in response && response.message ? String(response.message) : 'Bot not found'
        return {
            bot: null,
            errorMessage: message
        }
    }

    const bot = mapBotResponse(response as Record<string, unknown>, uuid)

    const statsResponse = await get_bot_stats(uuid)
    let stats: BotStats | null = null
    let statsError: string | null = null

    if (
        statsResponse &&
        typeof statsResponse === 'object' &&
        'incoming_messages' in statsResponse &&
        'outgoing_messages' in statsResponse
    ) {
        const incomingRaw = Number(
            (statsResponse as Record<string, unknown>).incoming_messages ?? 0
        )
        const outgoingRaw = Number(
            (statsResponse as Record<string, unknown>).outgoing_messages ?? 0
        )

        stats = {
            incoming_messages:
                Number.isFinite(incomingRaw) && incomingRaw >= 0 ? Math.trunc(incomingRaw) : 0,
            outgoing_messages:
                Number.isFinite(outgoingRaw) && outgoingRaw >= 0 ? Math.trunc(outgoingRaw) : 0
        }
    } else if (
        statsResponse &&
        typeof statsResponse === 'object' &&
        'status' in statsResponse &&
        statsResponse.status === 'error'
    ) {
        statsError =
            'message' in statsResponse && statsResponse.message
                ? String(statsResponse.message)
                : 'Unable to load stats'
    }

    return {
        bot,
        stats,
        statsError
    }
}
