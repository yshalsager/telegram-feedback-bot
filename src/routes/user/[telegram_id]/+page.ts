import {error} from '@sveltejs/kit'
import {get_user_detail} from '$lib/api.js'
import {locales} from '$lib/i18n'
import {mapUserResponse} from '$lib/mappers/user'
import type {PageLoad} from './$types'

export const load: PageLoad = async ({params}) => {
    const telegramParam = params.telegram_id
    const telegramId = Number(telegramParam ?? '')

    if (!Number.isFinite(telegramId) || telegramId <= 0) {
        throw error(400, 'Invalid Telegram ID')
    }

    const response = await get_user_detail(telegramId)

    if (
        response &&
        typeof response === 'object' &&
        'status' in response &&
        response.status === 'error'
    ) {
        const message =
            'message' in response && response.message ? String(response.message) : 'User not found'
        return {
            user: null,
            errorMessage: message
        }
    }

    const user = mapUserResponse(
        response as Record<string, unknown>,
        telegramId,
        locales[0] || 'en'
    )

    return {
        user
    }
}
