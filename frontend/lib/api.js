import {get} from 'svelte/store'
import {session} from '$lib/stores.svelte.js'

/**
 * Get the CSRF token
 * @returns {Promise<string | undefined>} - The CSRF token
 */
export async function csrf_token() {
    await fetch('/api/csrf/')
    const csrfToken = getCookie('csrftoken')
    return csrfToken
}

/**
 * Get a cookie value by name
 * @param {string} name - The cookie name
 * @returns {string | undefined} - The cookie value or undefined if not found
 */
function getCookie(name) {
    const cookies = document.cookie.split('; ')
    for (const cookie of cookies) {
        const [key, value] = cookie.split('=')
        if (key === name) return value
    }
    return undefined
}

/**
 * Get the authorization headers
 * @returns {Record<string, string>} - The authorization headers
 */
function get_authorization_headers() {
    return {
        'Content-Type': 'application/json',
        'X-CSRFToken': get(session).csrfToken || '',
        Authorization: `Bearer ${get(session).data?.raw || ''}`
    }
}

/**
 * Validate the user session
 * @returns {Promise<boolean>} - True if the user is valid, false otherwise
 */
export async function validate_user() {
    const response = await fetch('/api/validate_user/', {
        method: 'POST',
        headers: get_authorization_headers()
    })
    const data = await response.json()
    return Boolean(data.status === 'success' && data.user)
}

/**
 * Set the language of the user
 * @param {string} language - The language to set
 * @returns {Promise<boolean>} - True if the language was set successfully, false otherwise
 */
export async function set_language(language) {
    const response = await fetch('/api/set_language/', {
        method: 'POST',
        headers: get_authorization_headers(),
        body: JSON.stringify({language})
    })
    const data = await response.json()
    return Boolean(data.status === 'success' && data.user?.language_code === language)
}

/**
 * Add a bot
 * @param {string} bot_token - The token of the bot to add
 * @param {boolean} enable_confirmations - Whether to enable confirmations
 * @param {string} start_message - The start message for the bot
 * @param {string} feedback_received_message - The feedback received message
 * @returns {Promise<object>} - The response data
 */
export async function add_bot(
    bot_token,
    enable_confirmations,
    start_message,
    feedback_received_message
) {
    const response = await fetch('/api/bot/', {
        method: 'POST',
        headers: get_authorization_headers(),
        body: JSON.stringify({
            bot_token,
            enable_confirmations,
            start_message,
            feedback_received_message
        })
    })
    const data = await response.json()
    return data
}

/**
 * Add a user
 * @param {number} telegram_id - The Telegram user ID
 * @param {string | null} username - Optional Telegram username without the @ symbol
 * @param {string} language_code - Preferred language code for the user
 * @param {boolean} is_whitelisted - Whether the user is allowed to access the mini app
 * @param {boolean} is_admin - Whether the user should receive admin privileges
 * @returns {Promise<object>} - The response data
 */
export async function add_user(telegram_id, username, language_code, is_whitelisted, is_admin) {
    const response = await fetch('/api/user/', {
        method: 'POST',
        headers: get_authorization_headers(),
        body: JSON.stringify({
            telegram_id,
            username,
            language_code,
            is_whitelisted,
            is_admin
        })
    })
    const data = await response.json()
    return data
}

export async function list_bots() {
    const response = await fetch('/api/bot/', {
        headers: get_authorization_headers()
    })
    const data = await response.json()
    return data
}

/**
 * Get a bot by UUID
 * @param {string} uuid - The UUID of the bot
 * @returns {Promise<object>} - The response data
 */
export async function get_bot(uuid) {
    const response = await fetch(`/api/bot/${uuid}/`, {
        headers: get_authorization_headers()
    })
    return response.json()
}

/**
 * Update a bot
 * @param {string} uuid - The UUID of the bot
 * @param {object} payload - The payload to update the bot with
 * @returns {Promise<object>} - The response data
 */
export async function update_bot(uuid, payload) {
    const response = await fetch(`/api/bot/${uuid}/`, {
        method: 'PUT',
        headers: get_authorization_headers(),
        body: JSON.stringify(payload)
    })
    return response.json()
}

/**
 * Delete a bot
 * @param {string} uuid - The UUID of the bot
 * @returns {Promise<object>} - The response data
 */
export async function delete_bot(uuid) {
    const response = await fetch(`/api/bot/${uuid}/`, {
        method: 'DELETE',
        headers: get_authorization_headers()
    })
    return response.json()
}

/**
 * List all users
 * @returns {Promise<object>} - The response data
 */
export async function list_users() {
    const response = await fetch('/api/user/', {
        headers: get_authorization_headers()
    })
    const data = await response.json()
    return data
}

/**
 * Retrieve a single user by Telegram ID
 * @param {number} telegram_id - The Telegram user ID
 * @returns {Promise<object>} - The response data
 */
export async function get_user_detail(telegram_id) {
    const response = await fetch(`/api/user/${telegram_id}/`, {
        headers: get_authorization_headers()
    })
    return response.json()
}

/**
 * Update an existing user
 * @param {number} telegram_id - The Telegram user ID
 * @param {Record<string, unknown>} payload - The fields to update
 * @returns {Promise<object>} - The response data
 */
export async function update_user_detail(telegram_id, payload) {
    const response = await fetch(`/api/user/${telegram_id}/`, {
        method: 'PUT',
        headers: get_authorization_headers(),
        body: JSON.stringify(payload)
    })
    return response.json()
}
