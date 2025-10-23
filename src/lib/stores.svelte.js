import {writable} from 'svelte/store'

/**
 * Session store for managing application initialization state
 * @type {import('svelte/store').Writable<{
 * loaded: boolean;
 * available: boolean;
 * isValid: boolean | undefined;
 * data: import('./telegram.js').InitData | undefined;
 * csrfToken: string | undefined;
 * isAdmin: boolean;
 * user: Record<string, unknown> | undefined;
 * }>}
 */

export const session = writable({
    loaded: false,
    available: true,
    isValid: undefined,
    data: undefined,
    csrfToken: undefined,
    isAdmin: false,
    user: undefined
})
