import type {Bot} from '$lib/types'

export function mapBotResponse(data: Record<string, unknown>, fallbackUuid: string): Bot {
    const confirmationsValue = data.confirmations_on
    const enabledValue = data.enabled

    return {
        uuid: typeof data.uuid === 'string' ? data.uuid : fallbackUuid,
        telegram_id: Number(data.telegram_id ?? 0),
        name: typeof data.name === 'string' ? data.name : '',
        username: typeof data.username === 'string' ? data.username : '',
        owner_username: typeof data.owner_username === 'string' ? data.owner_username : '',
        owner_telegram_id: Number(data.owner_telegram_id ?? 0),
        start_message: typeof data.start_message === 'string' ? data.start_message : '',
        feedback_received_message:
            typeof data.feedback_received_message === 'string'
                ? data.feedback_received_message
                : '',
        confirmations_on:
            typeof confirmationsValue === 'boolean'
                ? confirmationsValue
                : Boolean(confirmationsValue),
        enabled: typeof enabledValue === 'boolean' ? enabledValue : Boolean(enabledValue),
        forward_chat_id:
            typeof data.forward_chat_id === 'number'
                ? data.forward_chat_id
                : data.forward_chat_id === null
                  ? null
                  : Number(data.forward_chat_id ?? null) || null,
        created_at: typeof data.created_at === 'string' ? data.created_at : '',
        updated_at: typeof data.updated_at === 'string' ? data.updated_at : ''
    }
}
