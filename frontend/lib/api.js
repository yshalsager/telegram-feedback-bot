import {session} from '$lib/stores.svelte.js'
import {get} from 'svelte/store'

/**
 * Get the CSRF token
 * @returns {Promise<string>} - The CSRF token
 */
export async function csrf_token() {
    const response = await fetch('/api/csrf/')
    const data = await response.json()
    return data.csrf_token
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
