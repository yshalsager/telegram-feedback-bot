<script lang="ts">
import {goto} from '$app/navigation'
import {resolve} from '$app/paths'
import type {EventPayload} from '@tma.js/sdk-svelte'
import {on} from '@tma.js/sdk-svelte'
import SettingsPage from '~/components/management/SettingsPage.svelte'
import UserAccessForm from '~/components/management/UserAccessForm.svelte'
import {showNotification} from '~/lib/telegram.js'
import {add_user} from '$lib/api.js'
import {Input} from '$lib/components/ui/input'
import {locale} from '$lib/i18n'
import {normalize_username} from '$lib/utils'

type AddUserResponse = {
    status?: string
    message?: unknown
    user?: {
        username?: string | null
        telegram_id?: number
    }
}

let telegramId = $state('')
let username = $state('')
let languageCode = $state($locale)
let isWhitelisted = $state(true)
let isAdmin = $state(false)

const isTelegramIdValid = $derived(telegramId.trim() === '' || /^\d+$/.test(telegramId.trim()))
const isFormValid = $derived(isTelegramIdValid && telegramId.trim() !== '')

let disableSubmit = $state(false)

const onUserSuccessfullyAdded = on('popup_closed', (payload: EventPayload<'popup_closed'>) => {
    if (payload.button_id === 'user_successfully_added_close') goto(resolve('/app'))
    onUserSuccessfullyAdded()
})

async function handleSaveUser() {
    disableSubmit = true
    const trimmedId = telegramId.trim()
    const normalizedUsername = normalize_username(username)
    const usernamePayload = normalizedUsername ? normalizedUsername : null

    const response = (await add_user(
        Number(trimmedId),
        usernamePayload,
        languageCode,
        isWhitelisted,
        isAdmin
    )) as AddUserResponse

    if (response?.status === 'success') {
        const userData = response.user ?? {}
        const identifier = userData.username
            ? `@${userData.username}`
            : `${userData.telegram_id ?? ''}`
        showNotification('', `Successfully updated access for ${identifier}.`, [
            {id: 'user_successfully_added_close', type: 'close'}
        ])
        telegramId = ''
        username = ''
        languageCode = $locale
        isWhitelisted = true
        isAdmin = false
    } else {
        const message = response?.message ? String(response.message) : 'Failed to add user'
        showNotification('', `❗ ${message}`, [{id: 'user_failed_to_add_close', type: 'close'}])
    }

    disableSubmit = false
}
</script>

<SettingsPage ariaLabel="Adding User interface" title="Add new user">
    <UserAccessForm
        isSubmitting={disableSubmit}
        onsubmit={handleSaveUser}
        submitDisabled={!isFormValid || disableSubmit}
        bind:username
        bind:languageCode
        bind:isWhitelisted
        bind:isAdmin
    >
        {#snippet before()}
            <div class="space-y-2">
                <label
                    class="mb-2 block text-start text-sm font-medium text-foreground"
                    for="telegram-id"
                >
                    User ID
                </label>
                <Input
                    id="telegram-id"
                    class={`w-full ${!isTelegramIdValid ? 'border-destructive focus-visible:ring-destructive/20' : ''}`}
                    aria-describedby={!isTelegramIdValid ? 'telegram-id-error' : undefined}
                    aria-invalid={!isTelegramIdValid}
                    aria-required="true"
                    dir="ltr"
                    inputmode="numeric"
                    pattern="\\d*"
                    placeholder="123456789"
                    required
                    type="text"
                    bind:value={telegramId}
                />
                {#if !isTelegramIdValid}
                    <p
                        id="telegram-id-error"
                        class="text-start text-sm text-destructive"
                        role="alert"
                    >
                        Enter a valid numeric Telegram user ID.
                    </p>
                {/if}
            </div>
        {/snippet}
    </UserAccessForm>
</SettingsPage>
