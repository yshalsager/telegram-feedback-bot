import type {User} from '$lib/types'

export function mapUserResponse(
    data: Record<string, unknown>,
    fallbackTelegramId: number,
    defaultLanguage = 'en'
): User {
    const isWhitelistedValue = data.is_whitelisted
    const isAdminValue = data.is_admin

    return {
        telegram_id: Number(data.telegram_id ?? fallbackTelegramId),
        username: typeof data.username === 'string' ? data.username : '',
        language_code:
            typeof data.language_code === 'string' ? data.language_code : defaultLanguage,
        is_whitelisted:
            typeof isWhitelistedValue === 'boolean'
                ? isWhitelistedValue
                : Boolean(isWhitelistedValue),
        is_admin: typeof isAdminValue === 'boolean' ? isAdminValue : Boolean(isAdminValue),
        created_at: typeof data.created_at === 'string' ? data.created_at : '',
        updated_at: typeof data.updated_at === 'string' ? data.updated_at : ''
    }
}
