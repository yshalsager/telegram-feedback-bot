import {error} from '@sveltejs/kit'
import {get_bot} from '$lib/api.js'
import {mapBotResponse} from '$lib/mappers/bot'
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

    return {
        bot
    }
}
