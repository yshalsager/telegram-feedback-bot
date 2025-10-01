<script lang="ts">
import {goto} from '$app/navigation'
import {resolve} from '$app/paths'
import {page} from '$app/state'
import {Loader, Trash2} from '@lucide/svelte'
import type {EventPayload} from '@telegram-apps/sdk-svelte'
import {on} from '@telegram-apps/sdk-svelte'
import {showNotification} from '~/lib/telegram.js'
import {delete_bot, update_bot} from '$lib/api.js'
import {Button} from '$lib/components/ui/button'
import * as Card from '$lib/components/ui/card/index.js'
import {Separator} from '$lib/components/ui/separator/index.js'
import {Switch} from '$lib/components/ui/switch'
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

const onBotDeleted = on('popup_closed', (payload: EventPayload<'popup_closed'>) => {
    if (payload.button_id === 'bot_deleted_success_close') goto(resolve('/'))
    onBotDeleted()
})

const data = pageData

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
</script>

{#if !data}
    <div class="flex min-h-screen items-center justify-center">
        <Loader class="size-6 animate-spin" />
    </div>
{:else if bot}
    <div
        class="mx-auto min-h-screen max-w-lg py-8"
        aria-label={`Managing bot ${bot.name}`}
        dir="auto"
        role="application"
    >
        <div class="mb-8 space-y-2 text-center">
            <h2 class="text-xl font-bold sm:text-2xl md:text-3xl lg:text-4xl xl:text-5xl">
                Manage bot
            </h2>
            <p class="text-sm text-muted-foreground">
                @{bot.username}
            </p>
        </div>

        <Card.Root class="mb-6 shadow-2xl backdrop-blur-sm">
            <div class="space-y-6 p-6">
                <div class="space-y-2">
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
                </div>

                <div class="space-y-2">
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
                </div>

                <Separator class="my-4" />

                <div
                    class="flex items-center justify-between rounded-lg bg-secondary/30 px-4 py-4 transition-colors hover:bg-secondary/50"
                >
                    <div class="space-y-0.5 text-start">
                        <p
                            id="confirmations-label"
                            class="block text-sm font-medium text-foreground"
                        >
                            Message received confirmations
                        </p>
                    </div>
                    <Switch
                        id="enable-confirmations-toggle"
                        class="ms-4 data-[state=checked]:bg-[var(--tg-theme-button-color)] data-[state=unchecked]:bg-muted-foreground/30"
                        aria-labelledby="confirmations-label"
                        bind:checked={enableConfirmations}
                    />
                </div>

                <div
                    class="flex items-center justify-between rounded-lg bg-secondary/30 px-4 py-4 transition-colors hover:bg-secondary/50"
                >
                    <div class="space-y-0.5 text-start">
                        <p id="bot-status-label" class="block text-sm font-medium text-foreground">
                            Bot status
                        </p>
                        <p class="text-xs text-muted-foreground">
                            {enabled ? 'Enabled' : 'Disabled'}
                        </p>
                    </div>
                    <Switch
                        id="bot-status-toggle"
                        class="ms-4 data-[state=checked]:bg-[var(--tg-theme-button-color)] data-[state=unchecked]:bg-muted-foreground/30"
                        aria-labelledby="bot-status-label"
                        bind:checked={enabled}
                    />
                </div>

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
        </Card.Root>
    </div>
{:else}
    <div class="flex min-h-screen items-center justify-center">
        <p class="text-sm text-muted-foreground">{loadError ?? 'Bot not found'}</p>
    </div>
{/if}
