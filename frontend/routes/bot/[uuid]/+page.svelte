<script lang="ts">
import {goto} from '$app/navigation'
import {resolve} from '$app/paths'
import {page} from '$app/state'
import {Loader, Trash2} from '@lucide/svelte'
import type {EventPayload} from '@telegram-apps/sdk-svelte'
import {on} from '@telegram-apps/sdk-svelte'
import SettingsPage from '~/components/management/SettingsPage.svelte'
import SwitchRow from '~/components/management/SwitchRow.svelte'
import {showNotification} from '~/lib/telegram.js'
import {delete_bot, unlink_bot_forward_chat, update_bot} from '$lib/api.js'
import {Button} from '$lib/components/ui/button'
import {Separator} from '$lib/components/ui/separator/index.js'
import {Textarea} from '$lib/components/ui/textarea'
import {formatCharacterCount} from '$lib/i18n'
import {mapBotResponse} from '$lib/mappers/bot'
import type {Bot} from '$lib/types.ts'
import type {PageData} from './$types'

type UpdateBotResponse = {
    uuid?: string
    message?: unknown
    [key: string]: unknown
}

const botUuid = $derived(page.params.uuid ?? '')
const pageData = page.data as PageData | undefined

let bot = $state<Bot | null>(null)
let enableConfirmations = $state(true)
let enabled = $state(true)
let startMessage = $state('')
let feedbackReceivedMessage = $state('')
let loadError = $state<string | null>(null)

const isFormValid = $derived(startMessage.trim() !== '' && feedbackReceivedMessage.trim() !== '')
const hasChanges = $derived(
    Boolean(
        bot &&
            (startMessage !== bot.start_message ||
                feedbackReceivedMessage !== bot.feedback_received_message ||
                enableConfirmations !== bot.confirmations_on ||
                enabled !== bot.enabled)
    )
)

let disableSubmit = $state(false)
let disableDelete = $state(false)
let unlink_in_progress = $state(false)

const onBotDeleted = on('popup_closed', (payload: EventPayload<'popup_closed'>) => {
    if (payload.button_id === 'bot_deleted_success_close') goto(resolve('/'))
    onBotDeleted()
})

const data = pageData

function formatTimestamp(value: string | null | undefined) {
    if (!value) return '—'
    const parsed = new Date(value)
    return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString()
}

if (data) {
    const initialError = data.errorMessage ?? null
    loadError = initialError
    if (initialError) {
        showNotification('', `❗ ${initialError}`)
    }

    if (data.bot) {
        bot = data.bot
        enableConfirmations = data.bot.confirmations_on
        enabled = data.bot.enabled
        startMessage = data.bot.start_message
        feedbackReceivedMessage = data.bot.feedback_received_message
    } else {
        bot = null
        enableConfirmations = true
        enabled = true
        startMessage = ''
        feedbackReceivedMessage = ''
    }
}

async function handleUpdateBot() {
    if (!bot) return
    disableSubmit = true
    const response = (await update_bot(botUuid, {
        enable_confirmations: enableConfirmations,
        start_message: startMessage,
        feedback_received_message: feedbackReceivedMessage,
        enabled
    })) as UpdateBotResponse
    if (response?.uuid === botUuid) {
        const updated = mapBotResponse(response as Record<string, unknown>, botUuid)
        bot = updated
        enableConfirmations = updated.confirmations_on
        enabled = updated.enabled
        startMessage = updated.start_message
        feedbackReceivedMessage = updated.feedback_received_message
        showNotification('', '✅ Bot updated successfully')
    } else {
        const message =
            response && response.message ? String(response.message) : 'Failed to update bot'
        showNotification('', `❗ ${message}`)
    }
    disableSubmit = false
}

async function handleDeleteBot() {
    if (!bot) return
    if (typeof window !== 'undefined') {
        const confirmed = window.confirm(`Delete @${bot.username}?`)
        if (!confirmed) return
    }
    disableDelete = true
    const response = await delete_bot(botUuid)
    if (response && 'status' in response && response.status === 'success') {
        showNotification('', '✅ Bot deleted successfully', [
            {id: 'bot_deleted_success_close', type: 'close'}
        ])
    } else {
        const message =
            response && 'message' in response && response.message
                ? String(response.message)
                : 'Failed to delete bot'
        showNotification('', `❗ ${message}`)
    }
    disableDelete = false
}

async function unlink_group() {
    if (!bot || bot.forward_chat_id === null) return
    unlink_in_progress = true
    const response = await unlink_bot_forward_chat(botUuid)
    if (response && 'status' in response && response.status === 'success') {
        bot = {...bot, forward_chat_id: null}
        showNotification('', '✅ Bot unlinked from group')
    } else {
        const message =
            response && 'message' in response && response.message
                ? String(response.message)
                : 'Failed to unlink bot from group'
        showNotification('', `❗ ${message}`)
    }
    unlink_in_progress = false
}
</script>

{#if !data}
    <div class="flex min-h-screen items-center justify-center">
        <Loader class="size-6 animate-spin" />
    </div>
{:else if bot}
    <SettingsPage ariaLabel={`Managing bot ${bot.name}`} dir="auto" title="Manage bot">
        {#snippet header()}
            <div class="space-y-2 text-center">
                <h2 class="text-xl font-bold sm:text-2xl md:text-3xl lg:text-4xl xl:text-5xl">
                    Manage bot
                </h2>
                <a
                    class="text-sm font-medium text-[var(--tg-theme-button-color)] underline"
                    href={`https://t.me/${bot?.username}`}
                    rel="noopener noreferrer"
                    target="_blank"
                >
                    @{bot?.username}
                </a>
            </div>
        {/snippet}
        <div class="space-y-6">
            <section class="space-y-3">
                <h3 class="text-start text-sm font-semibold text-foreground">Bot information</h3>
                <div class="space-y-3 rounded-lg bg-secondary/20 px-4 py-4 text-sm">
                    <div class="flex items-center justify-between gap-3">
                        <span class="text-muted-foreground">Telegram ID</span>
                        <span class="font-medium text-foreground">
                            {bot?.telegram_id ? bot?.telegram_id.toLocaleString() : '—'}
                        </span>
                    </div>
                    <div class="flex flex-wrap items-center justify-between gap-3">
                        <span class="text-muted-foreground">Owner</span>
                        {#if bot?.owner_telegram_id}
                            <a
                                class="font-medium text-[var(--tg-theme-button-color)] underline"
                                href={resolve(`/user/${bot?.owner_telegram_id}`)}
                            >
                                {bot?.owner_username
                                    ? `@${bot.owner_username}`
                                    : bot.owner_telegram_id.toLocaleString()}
                            </a>
                        {:else}
                            <span class="font-medium text-foreground">
                                {bot?.owner_username ? `@${bot?.owner_username}` : '—'}
                            </span>
                        {/if}
                    </div>
                    <div class="flex items-center justify-between gap-3">
                        <span class="text-muted-foreground">Created</span>
                        <span class="font-medium text-foreground">
                            {formatTimestamp(bot?.created_at)}
                        </span>
                    </div>
                    <div class="flex items-center justify-between gap-3">
                        <span class="text-muted-foreground">Updated</span>
                        <span class="font-medium text-foreground">
                            {formatTimestamp(bot?.updated_at)}
                        </span>
                    </div>
                </div>
            </section>
            <Separator class="my-4" />

            <section class="space-y-2">
                <label
                    class="mb-2 block text-start text-sm font-medium text-foreground"
                    for="start-message"
                >
                    Start message
                </label>
                <Textarea
                    id="start-message"
                    class="min-h-[80px] w-full resize-none"
                    maxlength="4096"
                    required
                    bind:value={startMessage}
                />
                <p class="text-end text-xs text-muted-foreground">
                    {formatCharacterCount(startMessage.length)}
                </p>
            </section>

            <section class="space-y-2">
                <label
                    class="mb-2 block text-start text-sm font-medium text-foreground"
                    for="feedback-message"
                >
                    Feedback received message
                </label>
                <Textarea
                    id="feedback-message"
                    class="min-h-[80px] w-full resize-none"
                    maxlength="4096"
                    required
                    bind:value={feedbackReceivedMessage}
                />
                <p class="text-end text-xs text-muted-foreground">
                    {formatCharacterCount(feedbackReceivedMessage.length)}
                </p>
            </section>

            <Separator class="my-4" />

            <SwitchRow
                id="enable-confirmations-toggle"
                label="Message received confirmations"
                bind:checked={enableConfirmations}
            />

            <SwitchRow
                id="bot-status-toggle"
                description={enabled ? 'Enabled' : 'Disabled'}
                label="Bot status"
                bind:checked={enabled}
            />

            <section class="space-y-3 rounded-lg bg-secondary/20 px-4 py-4 text-sm">
                <div class="space-y-1 text-start">
                    <h3 class="text-sm font-semibold text-foreground">Forwarding destination</h3>
                    <p class="text-sm text-muted-foreground">
                        {bot?.forward_chat_id !== null && bot?.forward_chat_id !== undefined
                            ? `Feedback is forwarded to chat ID ${bot.forward_chat_id.toLocaleString()}.`
                            : 'Add this bot to a group to link it automatically, otherwise it sends messages to bot owner.'}
                    </p>
                </div>
                {#if bot?.forward_chat_id !== null && bot?.forward_chat_id !== undefined}
                    <Button
                        class="h-10 w-full text-base font-medium"
                        disabled={unlink_in_progress}
                        onclick={unlink_group}
                        variant="secondary"
                    >
                        {#if unlink_in_progress}
                            <Loader class="size-4 animate-spin" />
                        {:else}
                            Unlink group
                        {/if}
                    </Button>
                {/if}
            </section>

            <Separator class="my-4" />

            <div class="flex flex-col gap-3 sm:flex-row">
                <Button
                    class="h-11 flex-1 text-base font-medium"
                    disabled={!bot || !isFormValid || disableSubmit || !hasChanges}
                    onclick={handleUpdateBot}
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
                    onclick={handleDeleteBot}
                    variant="destructive"
                >
                    {#if disableDelete}
                        <Loader class="size-4 animate-spin" />
                    {:else}
                        <Trash2 class="size-4" />
                        Delete bot
                    {/if}
                </Button>
            </div>
        </div>
    </SettingsPage>
{:else}
    <div class="flex min-h-screen items-center justify-center">
        <p class="text-sm text-muted-foreground">{loadError ?? 'Bot not found'}</p>
    </div>
{/if}
