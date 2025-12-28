<script lang="ts">
import {goto} from '$app/navigation'
import {resolve} from '$app/paths'
import {page} from '$app/state'
import {Loader, Trash2} from '@lucide/svelte'
import SettingsPage from '~/components/management/SettingsPage.svelte'
import UserAccessForm from '~/components/management/UserAccessForm.svelte'
import {showNotification} from '~/lib/telegram.js'
import {delete_user, update_user_detail} from '$lib/api.js'
import {Button} from '$lib/components/ui/button'
import {Separator} from '$lib/components/ui/separator'
import {locale, locales} from '$lib/i18n'
import {mapUserResponse} from '$lib/mappers/user'
import type {User} from '$lib/types.ts'
import {normalize_username} from '$lib/utils'
import type {PageData} from './$types'

type UpdateUserResponse = {
    status?: string
    user?: unknown
    message?: unknown
}

type DeleteUserResponse = {
    status?: string
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
let disableDelete = $state(false)

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
        (normalize_username(username) !== (user.username ?? '') ||
            languageCode !== user.language_code ||
            isWhitelisted !== user.is_whitelisted ||
            isAdmin !== user.is_admin)
    )
)

async function handleUpdateUser() {
    if (!user) return
    const normalizedUsername = normalize_username(username)
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

async function handleDeleteUser() {
    if (!user) return

    if (typeof window !== 'undefined') {
        const confirmed = window.confirm(
            `Delete ${user.username ? `@${user.username}` : user.telegram_id}?`
        )
        if (!confirmed) return
    }

    disableDelete = true
    const response = (await delete_user(telegramId)) as DeleteUserResponse

    if (response?.status === 'success') {
        showNotification('', '✅ User deleted successfully')
        disableDelete = false
        await goto(resolve('/app'))
        return
    }

    const message = response?.message ? String(response.message) : 'Failed to delete user'
    showNotification('', `❗ ${message}`)
    disableDelete = false
}
</script>

{#if !data}
    <div class="flex min-h-screen items-center justify-center">
        <Loader class="size-6 animate-spin" />
    </div>
{:else if user}
    <SettingsPage
        ariaLabel={`Managing user ${user.username ? `@${user.username}` : user.telegram_id}`}
        title="Manage user"
    >
        {#snippet header()}
            <div class="space-y-2 text-center">
                <h2 class="text-xl font-bold sm:text-2xl md:text-3xl lg:text-4xl xl:text-5xl">
                    Manage user
                </h2>
                {#if user?.username}
                    <div class="flex flex-col items-center gap-1 text-sm">
                        <a
                            class="font-medium text-[var(--tg-theme-button-color)] underline"
                            href={`https://t.me/${user.username}`}
                            rel="noopener noreferrer"
                            target="_blank"
                        >
                            @{user.username}
                        </a>
                        <a
                            class="text-xs text-[var(--tg-theme-button-color)] underline"
                            href={`tg://user?id=${user.telegram_id}`}
                        >
                            ID: {user.telegram_id.toLocaleString()}
                        </a>
                    </div>
                {:else}
                    <a
                        class="text-sm font-medium text-[var(--tg-theme-button-color)] underline"
                        href={`tg://user?id=${user?.telegram_id}`}
                    >
                        {user?.telegram_id.toLocaleString()}
                    </a>
                {/if}
            </div>
        {/snippet}

        <UserAccessForm
            isSubmitting={disableSubmit}
            onsubmit={handleUpdateUser}
            showSubmitButton={false}
            submitDisabled={!hasChanges || disableSubmit}
            submitLabel="Save changes"
            bind:username
            bind:languageCode
            bind:isWhitelisted
            bind:isAdmin
        />

        <Separator class="my-4" />

        <div class="flex flex-col gap-3 sm:flex-row">
            <Button
                class="h-11 flex-1 text-base font-medium"
                disabled={!user || !hasChanges || disableSubmit}
                onclick={handleUpdateUser}
            >
                {#if disableSubmit}
                    <Loader class="size-4 animate-spin" />
                {:else}
                    Save
                {/if}
            </Button>
            <Button
                class="h-11 flex-1 text-base font-medium"
                disabled={disableDelete}
                onclick={handleDeleteUser}
                variant="destructive"
            >
                {#if disableDelete}
                    <Loader class="size-4 animate-spin" />
                {:else}
                    <Trash2 class="size-4" />
                    Delete user
                {/if}
            </Button>
        </div>
    </SettingsPage>
{:else}
    <div class="flex min-h-screen items-center justify-center">
        <p class="text-sm text-muted-foreground">{loadError ?? 'User not found.'}</p>
    </div>
{/if}
