import {goto} from '$app/navigation'
import {resolve} from '$app/paths'
import {
    backButton,
    init,
    initData,
    isTMA,
    mainButton,
    miniApp,
    popup,
    settingsButton,
    themeParams,
    viewport
} from '@telegram-apps/sdk-svelte'
import {mockEnvInDev} from '$lib/telegram_debug.js'
import {session} from './stores.svelte'

export async function initSDK() {
    try {
        if (!(await isTMA('complete'))) mockEnvInDev()
        await init()
        if (!miniApp.ready.isAvailable()) {
            console.log('❌ Mini App is not available')
            return
        }
        await miniApp.ready()
        if (miniApp.bindCssVars.isAvailable()) miniApp.bindCssVars()
        if (themeParams.mountSync.isAvailable()) themeParams.mountSync()
        if (themeParams.bindCssVars.isAvailable()) themeParams.bindCssVars()
        if (viewport.mount.isAvailable()) viewport.mount()
        if (viewport.bindCssVars.isAvailable()) viewport.bindCssVars()
        if (viewport.isMounted()) viewport.expand()
        if (mainButton.mount.isAvailable()) mainButton.mount()
        if (settingsButton.isSupported() && settingsButton.mount.isAvailable()) {
            settingsButton.mount()
            settingsButton.show()
            settingsButton.onClick(() => goto(resolve('/settings')))
        }
        if (backButton.isSupported() && backButton.mount.isAvailable()) {
            backButton.mount()
            backButton.show()
            backButton.onClick(() => history.back())
        }
        session.update(state => ({...state, loaded: true}))
        initData.restore()
    } catch (error) {
        console.error('❌ Telegram SDK initialization error:', error)
        session.update(state => ({...state, available: false}))
    }
}

/**
 * @typedef {Object} InitData
 * @property {string | undefined} queryId
 * @property {import('@telegram-apps/sdk-svelte').User | undefined} user
 * @property {import('@telegram-apps/sdk-svelte').User | undefined} receiver
 * @property {import('@telegram-apps/sdk-svelte').Chat | undefined} chat
 * @property {import('@telegram-apps/sdk-svelte').ChatType | undefined} chatType
 * @property {string | undefined} chatInstance
 * @property {string | undefined} startParam
 * @property {number | undefined} canSendAfter
 * @property {Date | undefined} authDate
 * @property {string | undefined} hash
 * @property {string | undefined} raw
 */
/**
 * Get the init data
 * @returns { InitData | null }
 */

export function getInitData() {
    try {
        return {
            queryId: initData.queryId(),
            user: initData.user(),
            receiver: initData.receiver(),
            chat: initData.chat(),
            chatType: initData.chatType(),
            chatInstance: initData.chatInstance(),
            startParam: initData.startParam(),
            canSendAfter: initData.canSendAfter(),
            authDate: initData.authDate(),
            hash: initData.hash(),
            raw: initData.raw()
        }
    } catch (error) {
        console.warn('Failed to get init data:', error)
        return null
    }
}

/**
 * Show a notification in the mini app
 * @param {string} title
 * @param {string} message
 * @param {import('@telegram-apps/sdk-svelte').ShowPopupOptionsButton[]} [buttons] - Optional array of buttons. Defaults to [{type: 'close'}]
 */
export function showNotification(title, message, buttons = [{type: 'close'}]) {
    try {
        popup.show({
            title,
            message,
            buttons
        })
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error)
        console.error(`Failed to show notification: ${errorMessage}`)
    }
}
