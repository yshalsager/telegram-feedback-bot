<script lang="ts">
import {page} from '$app/state'
import {Loader} from '@lucide/svelte'
import SettingsPage from '~/components/management/SettingsPage.svelte'
import UserAccessForm from '~/components/management/UserAccessForm.svelte'
import {showNotification} from '~/lib/telegram.js'
import {update_user_detail} from '$lib/api.js'
import {locale, locales} from '$lib/i18n'
import {mapUserResponse} from '$lib/mappers/user'
import type {User} from '$lib/types.ts'
import type {PageData} from './$types'

type UpdateUserResponse = {
    status?: string
    user?: unknown
    message?: unknown
}

const telegramId = $derived(Number(page.params.telegram_id ?? ''))
const pageData = page.data as PageData | undefined

let user = $state<User | null>(null)
let disableSubmit = $state(false)
let username = $state('')
let languageCode = $state($locale)
let isWhitelisted = $state(true)
let isAdmin = $state(false)
let loadError = $state<string | null>(pageData?.errorMessage ?? null)

function normalizeUsername(value: string) {
    const trimmed = value.trim()
    return trimmed.startsWith('@') ? trimmed.slice(1) : trimmed
}
const data = pageData

if (data) {
    const initialError = data.errorMessage ?? null
    loadError = initialError
    if (initialError) {
        showNotification('', `❗ ${initialError}`)
    }

    if (data.user) {
        user = data.user
        username = data.user.username
        languageCode = data.user.language_code
        isWhitelisted = data.user.is_whitelisted
        isAdmin = data.user.is_admin
    } else {
        user = null
        username = ''
        languageCode = $locale
        isWhitelisted = true
        isAdmin = false
    }
}

const hasChanges = $derived(
    Boolean(
        user &&
            (normalizeUsername(username) !== (user.username ?? '') ||
                languageCode !== user.language_code ||
                isWhitelisted !== user.is_whitelisted ||
                isAdmin !== user.is_admin)
    )
)

async function handleUpdateUser() {
    if (!user) return
    const normalizedUsername = normalizeUsername(username)
    const updates: Record<string, unknown> = {}

    if (normalizedUsername !== (user.username ?? '')) updates.username = normalizedUsername
    if (languageCode !== user.language_code) updates.language_code = languageCode
    if (isWhitelisted !== user.is_whitelisted) updates.is_whitelisted = isWhitelisted
    if (isAdmin !== user.is_admin) updates.is_admin = isAdmin

    if (Object.keys(updates).length === 0) {
        showNotification('', 'No changes to update.')
        return
    }

    disableSubmit = true
    const response = (await update_user_detail(telegramId, updates)) as UpdateUserResponse
    if (response?.status === 'success' && response.user) {
        const updated = mapUserResponse(
            response.user as Record<string, unknown>,
            telegramId,
            locales[0] || 'en'
        )
        user = updated
        username = updated.username
        languageCode = updated.language_code
        isWhitelisted = updated.is_whitelisted
        isAdmin = updated.is_admin
        showNotification('', '✅ User updated successfully')
    } else {
        const message =
            response && response.message ? String(response.message) : 'Failed to update user'
        showNotification('', `❗ ${message}`)
    }
    disableSubmit = false
}
</script>

{#if !data}
    <div class="flex min-h-screen items-center justify-center">
        <Loader class="size-6 animate-spin" />
    </div>
{:else if user}
    <SettingsPage
        ariaLabel={`Managing user ${user.username ? `@${user.username}` : user.telegram_id}`}
        subtitle={`Telegram ID: ${user.telegram_id}`}
        title="Manage user"
    >
        <UserAccessForm
            isSubmitting={disableSubmit}
            onsubmit={handleUpdateUser}
            submitDisabled={!hasChanges || disableSubmit}
            submitLabel="Save changes"
            bind:username
            bind:languageCode
            bind:isWhitelisted
            bind:isAdmin
        />
    </SettingsPage>
{:else}
    <div class="flex min-h-screen items-center justify-center">
        <p class="text-sm text-muted-foreground">{loadError ?? 'User not found.'}</p>
    </div>
{/if}
