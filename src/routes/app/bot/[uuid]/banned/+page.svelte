<script lang="ts">
import {goto} from '$app/navigation'
import {resolve} from '$app/paths'
import {page} from '$app/state'
import {Loader} from '@lucide/svelte'
import SettingsPage from '~/components/management/SettingsPage.svelte'
import {showNotification} from '~/lib/telegram.js'
import {ban_user, list_banned_users, unban_user} from '$lib/api.js'
import {Button} from '$lib/components/ui/button'
import {Input} from '$lib/components/ui/input'
import {Separator} from '$lib/components/ui/separator'
import {Textarea} from '$lib/components/ui/textarea'
import type {BannedUser, Bot} from '$lib/types.ts'
import type {PageData} from './$types'

type BanResponse = {
    status?: string
    message?: unknown
    user_telegram_id?: number
    created?: boolean
}

type UnbanResponse = {
    status?: string
    message?: unknown
    user_telegram_id?: number
    removed?: boolean
}

const botUuid = $derived(page.params.uuid ?? '')
const data = page.data as PageData | undefined

let bot = $state<Bot | null>(data?.bot ?? null)
let bannedUsers = $state<BannedUser[]>(data?.bannedUsers ?? [])
let bannedError = $state<string | null>(data?.bannedError ?? null)
let loadError = $state<string | null>(data?.errorMessage ?? null)
let newBanId = $state('')
let newBanReason = $state('')
let submitting = $state(false)
let unbanTarget = $state<number | null>(null)

const trimmedId = $derived(newBanId.trim())
const isIdValid = $derived(trimmedId !== '' && /^\d+$/.test(trimmedId))

function normalizeBannedUsers(payload: unknown): BannedUser[] {
    if (!Array.isArray(payload)) return []
    return payload
        .map(entry => {
            if (!entry || typeof entry !== 'object') return null
            const raw = entry as Record<string, unknown>
            const userId = Number(raw.user_telegram_id)
            if (!Number.isFinite(userId) || userId <= 0) return null
            const created_at = typeof raw.created_at === 'string' ? raw.created_at : ''
            const reasonRaw = raw.reason ?? null
            const reason = typeof reasonRaw === 'string' ? reasonRaw : null
            return {
                user_telegram_id: Math.trunc(userId),
                created_at,
                reason
            }
        })
        .filter(Boolean) as BannedUser[]
}

function formatTimestamp(value: string) {
    if (!value) return '—'
    const parsed = new Date(value)
    return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString()
}

async function reloadBannedUsers() {
    const response = await list_banned_users(botUuid)
    if (
        response &&
        typeof response === 'object' &&
        'status' in response &&
        response.status === 'error'
    ) {
        const message =
            'message' in response && response.message
                ? String(response.message)
                : 'Unable to load banned users'
        bannedError = message
        bannedUsers = []
        return
    }
    bannedUsers = normalizeBannedUsers(response)
    bannedError = null
}

async function handleBan() {
    if (!bot || !isIdValid || submitting) return
    submitting = true
    const userId = Number(trimmedId)
    const response = (await ban_user(botUuid, userId, newBanReason)) as BanResponse
    if (response && response.status === 'success') {
        const message = response.message ? String(response.message) : 'User banned'
        showNotification('', `✅ ${message}`)
        newBanId = ''
        newBanReason = ''
        await reloadBannedUsers()
    } else {
        const message =
            response && response.message ? String(response.message) : 'Failed to ban user'
        showNotification('', `❗ ${message}`)
    }
    submitting = false
}

async function handleUnban(userId: number) {
    if (!bot || unbanTarget !== null) return
    unbanTarget = userId
    const response = (await unban_user(botUuid, userId)) as UnbanResponse
    if (response && response.status === 'success') {
        const message = response.message ? String(response.message) : 'User updated'
        const prefix = response.removed ? '✅' : 'ℹ️'
        showNotification('', `${prefix} ${message}`)
        await reloadBannedUsers()
    } else {
        const message =
            response && response.message ? String(response.message) : 'Failed to unban user'
        showNotification('', `❗ ${message}`)
    }
    unbanTarget = null
}
</script>

{#if !data}
    <div class="flex min-h-screen items-center justify-center">
        <Loader class="size-6 animate-spin" />
    </div>
{:else if !bot}
    <div class="flex min-h-screen items-center justify-center">
        <p class="text-sm text-muted-foreground">{loadError ?? 'Bot not found'}</p>
    </div>
{:else}
    <SettingsPage
        ariaLabel={`Managing banned users for ${bot.name}`}
        dir="auto"
        title="Manage banned users"
    >
        {#snippet header()}
            <div class="space-y-2 text-center">
                <h2 class="text-xl font-bold sm:text-2xl md:text-3xl lg:text-4xl xl:text-5xl">
                    Manage banned users
                </h2>
                <a
                    class="text-sm font-medium text-[var(--tg-theme-button-color)] underline"
                    href={resolve(`/app/bot/${botUuid}`)}
                >
                    Back to bot management
                </a>
                <p class="text-xs text-muted-foreground">@{bot.username}</p>
            </div>
        {/snippet}

        <div class="space-y-6">
            <section class="space-y-3">
                <h3 class="text-start text-sm font-semibold text-foreground">Ban a user</h3>
                <p class="text-sm text-muted-foreground">
                    Enter a Telegram user ID to prevent them from sending feedback through this bot.
                </p>
                <div class="flex flex-col gap-3 sm:flex-row">
                    <Input
                        id="ban-user-id"
                        class="flex-1"
                        aria-label="Telegram user ID"
                        autocomplete="off"
                        inputmode="numeric"
                        placeholder="123456789"
                        bind:value={newBanId}
                    />
                    <Button
                        class="h-11 sm:w-40"
                        disabled={!isIdValid || submitting}
                        onclick={handleBan}
                    >
                        {#if submitting}
                            <Loader class="size-4 animate-spin" />
                        {:else}
                            Ban user
                        {/if}
                    </Button>
                </div>
                {#if newBanId && !isIdValid}
                    <p class="text-sm text-destructive">Enter a valid numeric user ID.</p>
                {/if}
                <Textarea
                    id="ban-reason"
                    class="min-h-[72px]"
                    aria-label="Ban reason"
                    maxlength={512}
                    placeholder="Reason (optional)"
                    bind:value={newBanReason}
                />
            </section>

            <Separator class="my-4" />

            <section class="space-y-3">
                <div class="flex items-center justify-between">
                    <h3 class="text-start text-sm font-semibold text-foreground">
                        Currently banned
                    </h3>
                    {#if bannedError}
                        <span class="text-xs font-medium text-destructive">{bannedError}</span>
                    {/if}
                </div>
                {#if bannedError}
                    <p class="text-sm text-muted-foreground">
                        Try reloading this page or banning a user to refresh the list.
                    </p>
                {:else if bannedUsers.length === 0}
                    <p class="text-sm text-muted-foreground">No banned users yet.</p>
                {:else}
                    <ul class="space-y-2">
                        {#each bannedUsers as entry (entry.user_telegram_id)}
                            <li
                                class="flex items-center justify-between rounded-lg bg-secondary/20 px-4 py-3 text-sm"
                            >
                                <div class="space-y-1 text-start">
                                    <p class="font-semibold text-foreground">
                                        {entry.user_telegram_id.toLocaleString()}
                                    </p>
                                    <p class="text-xs text-muted-foreground">
                                        Banned {formatTimestamp(entry.created_at)}
                                    </p>
                                    <p class="text-xs text-muted-foreground" dir="auto">
                                        Reason: {entry.reason && entry.reason.trim() !== ''
                                            ? entry.reason
                                            : 'Not provided'}
                                    </p>
                                </div>
                                <Button
                                    class="h-9 min-w-24"
                                    disabled={unbanTarget === entry.user_telegram_id}
                                    onclick={() => handleUnban(entry.user_telegram_id)}
                                    variant="secondary"
                                >
                                    {#if unbanTarget === entry.user_telegram_id}
                                        <Loader class="size-4 animate-spin" />
                                    {:else}
                                        Unban
                                    {/if}
                                </Button>
                            </li>
                        {/each}
                    </ul>
                {/if}
            </section>
        </div>

        {#snippet footer()}
            <div class="mx-auto mt-6 flex max-w-lg justify-center">
                <Button onclick={() => goto(resolve(`/app/bot/${botUuid}`))} variant="ghost">
                    Return to bot settings
                </Button>
            </div>
        {/snippet}
    </SettingsPage>
{/if}
