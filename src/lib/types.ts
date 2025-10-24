export type Bot = {
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
    antiflood_enabled: boolean
    antiflood_seconds: number
    communication_mode: 'standard' | 'private' | 'anonymous'
    forward_chat_id: number | null
    created_at: string
    updated_at: string
}

export type User = {
    telegram_id: number
    username: string
    language_code: string
    is_whitelisted: boolean
    is_admin: boolean
    created_at: string
    updated_at: string
}

export type ListItem = Bot | User

export type BotStats = {
    incoming_messages: number
    outgoing_messages: number
}

export type BannedUser = {
    user_telegram_id: number
    created_at: string
    reason: string | null
}

export type LanguageOption = {
    locale: string
    name: string
}
