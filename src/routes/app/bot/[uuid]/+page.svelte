<script lang="ts">
import {goto} from '$app/navigation'
import {resolve} from '$app/paths'
import {page} from '$app/state'
import {Loader, Trash2} from '@lucide/svelte'
import type {EventPayload} from '@telegram-apps/sdk-svelte'
import {on} from '@telegram-apps/sdk-svelte'
import BotMessageField from '~/components/management/BotMessageField.svelte'
import CommunicationModeSection from '~/components/management/CommunicationModeSection.svelte'
import SettingsPage from '~/components/management/SettingsPage.svelte'
import SwitchRow from '~/components/management/SwitchRow.svelte'
import {showNotification} from '~/lib/telegram.js'
import {delete_bot, unlink_bot_forward_chat, update_bot} from '$lib/api.js'
import {Button} from '$lib/components/ui/button'
import {Input} from '$lib/components/ui/input'
import {Separator} from '$lib/components/ui/separator'
import type {CommunicationMode} from '$lib/constants/communication_mode'
import {mapBotResponse} from '$lib/mappers/bot'
import type {Bot, BotStats} from '$lib/types.ts'
import type {PageData} from './$types'

type UpdateBotResponse = {
    uuid?: string
    message?: unknown
    [key: string]: unknown
}

const botUuid = $derived(page.params.uuid ?? '')
const pageData = page.data as PageData | undefined

let bot = $state<Bot | null>(null)
let enabled = $state(true)
let startMessage = $state('')
let feedbackReceivedMessage = $state('')
let allow_photo_messages = $state(true)
let allow_video_messages = $state(true)
let allow_voice_messages = $state(true)
let allow_document_messages = $state(true)
let allow_sticker_messages = $state(true)
let communication_mode = $state<CommunicationMode>('standard')
let antiflood_enabled = $state(false)
let antiflood_seconds = $state(60)
let pendingToken = $state('')
let loadError = $state<string | null>(null)
let stats = $state<BotStats | null>(null)
let statsError = $state<string | null>(null)

const trimmedPendingToken = $derived(pendingToken.trim())
const isFormValid = $derived(startMessage.trim() !== '' && feedbackReceivedMessage.trim() !== '')
const hasChanges = $derived(
    Boolean(
        bot &&
            (startMessage !== bot.start_message ||
                feedbackReceivedMessage !== bot.feedback_received_message ||
                enabled !== bot.enabled ||
                communication_mode !== bot.communication_mode ||
                allow_photo_messages !== bot.allow_photo_messages ||
                allow_video_messages !== bot.allow_video_messages ||
                allow_voice_messages !== bot.allow_voice_messages ||
                allow_document_messages !== bot.allow_document_messages ||
                allow_sticker_messages !== bot.allow_sticker_messages ||
                antiflood_enabled !== bot.antiflood_enabled ||
                antiflood_seconds !== bot.antiflood_seconds ||
                trimmedPendingToken !== '')
    )
)

let disableSubmit = $state(false)
let disableDelete = $state(false)
let unlink_in_progress = $state(false)

const onBotDeleted = on('popup_closed', (payload: EventPayload<'popup_closed'>) => {
    if (payload.button_id === 'bot_deleted_success_close') goto(resolve('/app'))
    onBotDeleted()
})

const data = pageData

function formatTimestamp(value: string | null | undefined) {
    if (!value) return '—'
    const parsed = new Date(value)
    return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString()
}

const formatCount = (value: number | null | undefined) =>
    typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString() : '0'

if (data) {
    const initialError = data.errorMessage ?? null
    loadError = initialError
    if (initialError) {
        showNotification('', `❗ ${initialError}`)
    }

    if (data.bot) {
        bot = data.bot
        enabled = data.bot.enabled
        startMessage = data.bot.start_message
        feedbackReceivedMessage = data.bot.feedback_received_message
        allow_photo_messages = data.bot.allow_photo_messages
        allow_video_messages = data.bot.allow_video_messages
        allow_voice_messages = data.bot.allow_voice_messages
        allow_document_messages = data.bot.allow_document_messages
        allow_sticker_messages = data.bot.allow_sticker_messages
        communication_mode = data.bot.communication_mode
        antiflood_enabled = data.bot.antiflood_enabled
        antiflood_seconds = data.bot.antiflood_seconds ?? 60
        pendingToken = ''
    } else {
        bot = null
        enabled = true
        startMessage = ''
        feedbackReceivedMessage = ''
        allow_photo_messages = true
        allow_video_messages = true
        allow_voice_messages = true
        allow_document_messages = true
        allow_sticker_messages = true
        communication_mode = 'standard'
        antiflood_enabled = false
        antiflood_seconds = 60
        pendingToken = ''
    }

    stats = data.stats ?? null
    statsError = data.statsError ?? null
}

async function handleUpdateBot() {
    if (!bot) return
    disableSubmit = true
    const normalizedCooldown = Number.isFinite(antiflood_seconds)
        ? Math.max(Math.trunc(antiflood_seconds), 1)
        : 60
    const response = (await update_bot(botUuid, {
        start_message: startMessage,
        feedback_received_message: feedbackReceivedMessage,
        enabled,
        allow_photo_messages,
        allow_video_messages,
        allow_voice_messages,
        allow_document_messages,
        allow_sticker_messages,
        communication_mode,
        antiflood_enabled,
        antiflood_seconds: normalizedCooldown,
        ...(trimmedPendingToken !== '' ? {bot_token: trimmedPendingToken} : {})
    })) as UpdateBotResponse
    if (response?.uuid === botUuid) {
        const updated = mapBotResponse(response as Record<string, unknown>, botUuid)
        bot = updated
        enabled = updated.enabled
        startMessage = updated.start_message
        feedbackReceivedMessage = updated.feedback_received_message
        allow_photo_messages = updated.allow_photo_messages
        allow_video_messages = updated.allow_video_messages
        allow_voice_messages = updated.allow_voice_messages
        allow_document_messages = updated.allow_document_messages
        allow_sticker_messages = updated.allow_sticker_messages
        communication_mode = updated.communication_mode
        antiflood_enabled = updated.antiflood_enabled
        antiflood_seconds = updated.antiflood_seconds
        pendingToken = ''
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
                                href={resolve(`/app/user/${bot?.owner_telegram_id}`)}
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
            <section class="space-y-3">
                <div class="flex items-center justify-between">
                    <h3 class="text-sm font-semibold text-foreground">Bot stats</h3>
                    {#if statsError}
                        <span class="text-xs font-medium text-destructive">{statsError}</span>
                    {/if}
                </div>
                <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <div class="space-y-1 rounded-lg bg-secondary/20 px-4 py-4 text-sm">
                        <span class="text-muted-foreground">Incoming messages</span>
                        <span class="block text-2xl font-semibold text-foreground">
                            {formatCount(stats?.incoming_messages)}
                        </span>
                    </div>
                    <div class="space-y-1 rounded-lg bg-secondary/20 px-4 py-4 text-sm">
                        <span class="text-muted-foreground">Outgoing messages</span>
                        <span class="block text-2xl font-semibold text-foreground">
                            {formatCount(stats?.outgoing_messages)}
                        </span>
                    </div>
                </div>
            </section>
            <Separator class="my-4" />

            <BotMessageField
                field_id="start-message"
                label="Start message"
                bind:value={startMessage}
            />

            <BotMessageField
                field_id="feedback-message"
                label="Feedback received message"
                bind:value={feedbackReceivedMessage}
            />

            <section class="space-y-2">
                <label
                    class="mb-2 block text-start text-sm font-medium text-foreground"
                    for="bot-token"
                >
                    Bot token
                </label>
                <Input
                    id="bot-token"
                    autocapitalize="none"
                    autocomplete="off"
                    autocorrect="off"
                    placeholder="Enter a new token to rotate"
                    spellcheck={false}
                    type="password"
                    bind:value={pendingToken}
                />
                <p class="text-xs text-muted-foreground">
                    Leave empty to keep the current token. Updating rotates it immediately.
                </p>
            </section>

            <CommunicationModeSection bind:value={communication_mode} />

            <Separator class="my-4" />

            <SwitchRow
                id="bot-status-toggle"
                description={enabled ? 'Enabled' : 'Disabled'}
                label="Bot status"
                bind:checked={enabled}
            />

            <div class="space-y-2">
                <SwitchRow
                    id="bot-antiflood-toggle"
                    description={antiflood_enabled ? 'Enabled' : 'Disabled'}
                    label="Anti-flood"
                    bind:checked={antiflood_enabled}
                />
                <div class="space-y-1">
                    <label
                        class="block text-xs font-medium text-foreground"
                        for="bot-antiflood-wait"
                    >
                        Anti-flood wait (seconds)
                    </label>
                    <Input
                        id="bot-antiflood-wait"
                        class="h-9"
                        disabled={!antiflood_enabled}
                        max="3600"
                        min="1"
                        step="1"
                        type="number"
                        bind:value={antiflood_seconds}
                    />
                    <p class="text-xs text-muted-foreground">
                        When enabled, users can send one message every {Number.isFinite(
                            antiflood_seconds
                        )
                            ? antiflood_seconds.toLocaleString()
                            : '—'} seconds and receive a warning if throttled.
                    </p>
                </div>
            </div>

            <section class="space-y-3 rounded-lg bg-secondary/20 px-4 py-4 text-sm">
                <div class="space-y-1 text-start">
                    <h3 class="text-sm font-semibold text-foreground">Media permissions</h3>
                    <p class="text-sm text-muted-foreground">
                        Choose which media types users can send to this bot.
                    </p>
                </div>
                <div class="space-y-2">
                    <SwitchRow
                        id="media-photos-toggle"
                        description={allow_photo_messages ? 'Allowed' : 'Blocked'}
                        label="Photos"
                        bind:checked={allow_photo_messages}
                    />
                    <SwitchRow
                        id="media-videos-toggle"
                        description={allow_video_messages ? 'Allowed' : 'Blocked'}
                        label="Videos"
                        bind:checked={allow_video_messages}
                    />
                    <SwitchRow
                        id="media-voice-toggle"
                        description={allow_voice_messages ? 'Allowed' : 'Blocked'}
                        label="Voice messages"
                        bind:checked={allow_voice_messages}
                    />
                    <SwitchRow
                        id="media-documents-toggle"
                        description={allow_document_messages ? 'Allowed' : 'Blocked'}
                        label="Files"
                        bind:checked={allow_document_messages}
                    />
                    <SwitchRow
                        id="media-stickers-toggle"
                        description={allow_sticker_messages ? 'Allowed' : 'Blocked'}
                        label="Stickers"
                        bind:checked={allow_sticker_messages}
                    />
                </div>
            </section>

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

            <section class="space-y-3 rounded-lg bg-secondary/20 px-4 py-4 text-sm">
                <div class="space-y-1 text-start">
                    <h3 class="text-sm font-semibold text-foreground">Banned users</h3>
                    <p class="text-sm text-muted-foreground">
                        Block or unblock people from sending feedback to this bot.
                    </p>
                </div>
                <Button
                    class="h-10 w-full text-base font-medium"
                    onclick={() => goto(resolve(`/app/bot/${botUuid}/banned`))}
                    variant="secondary"
                >
                    Manage banned users
                </Button>
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
