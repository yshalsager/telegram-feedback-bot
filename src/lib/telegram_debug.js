import {emitEvent, mockTelegramEnv, setDebug} from '@tma.js/sdk-svelte'
import {env} from '$env/dynamic/public'
import eruda from 'eruda'

const DEBUG = env.PUBLIC_DEBUG === 'true' || false
setDebug(DEBUG)

if (DEBUG) {
    eruda.init()
    eruda.position({
        x: window.innerWidth - 70,
        y: 100
    })
}

const noInsets = {
    left: 0,
    top: 0,
    bottom: 0,
    right: 0
}
/**
 * @type {Record<string, string>}
 */
const mockThemeParams = {
    accent_text_color: '#6ab2f2',
    bg_color: '#17212b',
    button_color: '#5288c1',
    button_text_color: '#ffffff',
    destructive_text_color: '#ec3942',
    header_bg_color: '#17212b',
    hint_color: '#708499',
    link_color: '#6ab3f3',
    secondary_bg_color: '#232e3c',
    section_bg_color: '#17212b',
    section_header_text_color: '#6ab3f3',
    subtitle_text_color: '#708499',
    text_color: '#f5f5f5'
}

export function mockEnvInDev() {
    if (!DEBUG) return

    mockTelegramEnv({
        launchParams: {
            tgWebAppThemeParams: mockThemeParams,
            tgWebAppData: new URLSearchParams([
                [
                    'user',
                    JSON.stringify({
                        id: 1,
                        first_name: 'Test',
                        last_name: 'Admin',
                        username: 'admin',
                        language_code: 'en',
                        is_premium: true
                    })
                ],
                ['hash', ''],
                ['signature', ''],
                ['auth_date', String(Math.floor(Date.now() / 1000))]
            ]),
            tgWebAppStartParam: 'debug',
            tgWebAppVersion: '9',
            tgWebAppPlatform: 'tdesktop'
        },
        onEvent(e) {
            if (e[0] === 'web_app_request_theme') {
                /** @type {any} */
                const _themeParams = mockThemeParams
                return emitEvent('theme_changed', {theme_params: _themeParams})
            }
            if (e[0] === 'web_app_request_viewport') {
                return emitEvent('viewport_changed', {
                    height: window.innerHeight,
                    width: window.innerWidth,
                    is_expanded: true,
                    is_state_stable: true
                })
            }
            if (e[0] === 'web_app_request_content_safe_area') {
                return emitEvent('content_safe_area_changed', noInsets)
            }
            if (e[0] === 'web_app_request_safe_area') {
                return emitEvent('safe_area_changed', noInsets)
            }
        }
    })
}
