// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
interface TelegramWebApp {
    initData: string
    initDataUnsafe: {
        user?: {
            id: number
            first_name: string
            last_name?: string
            username?: string
            language_code?: string
            is_premium?: boolean
        }
    }
    version: string
    platform: string
    colorScheme: 'light' | 'dark'
    themeParams: {
        bg_color?: string
        text_color?: string
        hint_color?: string
        link_color?: string
        button_color?: string
        button_text_color?: string
        secondary_bg_color?: string
        header_bg_color?: string
        accent_text_color?: string
        section_bg_color?: string
        section_header_text_color?: string
        subtitle_text_color?: string
        destructive_text_color?: string
    }
    isExpanded: boolean
    viewportHeight: number
    viewportStableHeight: number
    headerColor: string
    backgroundColor: string
    isClosingConfirmationEnabled: boolean
    isVerticalSwipesEnabled: boolean

    ready(): void
    expand(): void
    close(): void
    sendData(data: string): void
    addToHomeScreen(): void
    showAlert(message: string, callback?: () => void): void
    showConfirm(message: string, callback?: (confirmed: boolean) => void): void
    showPopup(
        params: {
            title?: string
            message: string
            buttons?: Array<{
                id?: string
                type?: 'default' | 'ok' | 'close' | 'cancel' | 'destructive'
                text?: string
            }>
        },
        callback?: (buttonId: string) => void
    ): void

    MainButton: {
        text: string
        color: string
        textColor: string
        isVisible: boolean
        isActive: boolean
        isProgressVisible: boolean
        setText(text: string): void
        onClick(callback: () => void): void
        offClick(callback: () => void): void
        show(): void
        hide(): void
        enable(): void
        disable(): void
        showProgress(leaveActive?: boolean): void
        hideProgress(): void
        setParams(params: {
            text?: string
            color?: string
            text_color?: string
            is_active?: boolean
            is_visible?: boolean
        }): void
    }

    BackButton: {
        isVisible: boolean
        onClick(callback: () => void): void
        offClick(callback: () => void): void
        show(): void
        hide(): void
    }

    SettingsButton: {
        isVisible: boolean
        onClick(callback: () => void): void
        offClick(callback: () => void): void
        show(): void
        hide(): void
    }

    onEvent(eventType: string, eventHandler: () => void): void
    offEvent(eventType: string, eventHandler: () => void): void
}

declare global {
    interface Window {
        Telegram: {
            WebApp: TelegramWebApp
        }
    }

    namespace App {
        // interface Error {}
        // interface Locals {}
        // interface PageData {}
        // interface PageState {}
        // interface Platform {}
    }
}

export {}
