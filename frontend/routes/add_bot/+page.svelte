<script lang="ts">
import {goto} from '$app/navigation'
import {add_bot} from '$lib/api.js'
import {Button} from '$lib/components/ui/button'
import * as Card from '$lib/components/ui/card/index.js'
import {Input} from '$lib/components/ui/input'
import {Separator} from '$lib/components/ui/separator/index.js'
import {Switch} from '$lib/components/ui/switch'
import {Textarea} from '$lib/components/ui/textarea'
import {m} from '$lib/paraglide/messages.js'
import {getLocale} from '$lib/paraglide/runtime.js'
import {Loader} from '@lucide/svelte'
import type {EventPayload} from '@telegram-apps/sdk-svelte'
import {on} from '@telegram-apps/sdk-svelte'
import {showNotification} from '~/lib/telegram.js'

let botToken = $state('')
let enableConfirmations = $state(true)
let startMessage = $state(m.default_start())
let feedbackReceivedMessage = $state(m.default_received())
let disableSubmit = $state(false)
let currentLocale = $state(getLocale())

// Bot token regex validation
const botTokenRegex = /^[0-9]{8,10}:[a-zA-Z0-9_-]{35}$/
let isTokenValid = $derived(botToken === '' || botTokenRegex.test(botToken))

// Form validation
let isFormValid = $derived(
    isTokenValid &&
        botToken !== '' &&
        startMessage.trim() !== '' &&
        feedbackReceivedMessage.trim() !== ''
)

// Format character count with locale-specific number formatting
function formatCharacterCount(count: number) {
    return `${Intl.NumberFormat(currentLocale).format(count)}/${Intl.NumberFormat(currentLocale).format(4096)} ${m.characters()}`
}

const onBotSuccessfullyAdded = on('popup_closed', (payload: EventPayload<'popup_closed'>) => {
    if (payload.button_id === 'bot_successfully_added_close') goto('/')
    onBotSuccessfullyAdded()
})

async function handleSaveBot() {
    disableSubmit = true
    console.log('Saving bot with token:', botToken, 'confirmations enabled:', enableConfirmations)
    const response = await add_bot(
        botToken,
        enableConfirmations,
        startMessage,
        feedbackReceivedMessage
    )
    if (response && 'status' in response && response.status === 'success') {
        showNotification('', m.bot_successfully_added({username: response.bot?.username || ''}), [
            {id: 'bot_successfully_added_close', type: 'close'}
        ])
    } else {
        const message =
            response && 'message' in response && response.message
                ? String(response.message)
                : m.bot_failed_to_add()
        showNotification('', `❗ ${message}`, [{id: 'bot_failed_to_add_close', type: 'close'}])
    }
    disableSubmit = false
}
</script>

<div
    class="mx-auto min-h-screen max-w-lg py-8"
    role="application"
    aria-label="Adding Bot interface"
    dir="auto"
>
    <!-- Header Section -->
    <div class="mb-8 text-center">
        <h2 class="text-xl font-bold sm:text-2xl md:text-3xl lg:text-4xl xl:text-5xl">
            {m.add_bot()}
        </h2>
    </div>

    <!-- Bot Configuration Card -->
    <Card.Root class="mb-6 shadow-2xl backdrop-blur-sm">
        <div class="p-6">
            <!-- Form Container -->
            <div class="space-y-6">
                <!-- Bot Token Input -->
                <div class="space-y-2">
                    <label
                        for="bot-token"
                        class="mb-2 block text-start text-sm font-medium text-foreground"
                    >
                        {m.bot_token()}
                    </label>
                    <Input
                        id="bot-token"
                        bind:value={botToken}
                        placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz123456789"
                        aria-required="true"
                        required
                        type="text"
                        dir="ltr"
                        class={`w-full ${!isTokenValid ? 'border-destructive focus-visible:ring-destructive/20' : ''}`}
                        aria-invalid={!isTokenValid}
                        aria-describedby={!isTokenValid ? 'token-error' : undefined}
                    />
                    {#if !isTokenValid}
                        <p
                            id="token-error"
                            class="text-start text-sm text-destructive"
                            role="alert"
                        >
                            {m.bot_token_hint()}
                        </p>
                    {/if}
                </div>

                <Separator class="my-6" />

                <!-- Start Message Input -->
                <div class="space-y-2">
                    <label
                        for="start-message"
                        class="mb-2 block text-start text-sm font-medium text-foreground"
                    >
                        {m.start_message()}
                    </label>
                    <Textarea
                        id="start-message"
                        bind:value={startMessage}
                        aria-required="true"
                        required
                        class="min-h-[80px] w-full resize-none"
                        maxlength="4096"
                    />
                    <p class="text-end text-xs text-muted-foreground">
                        {formatCharacterCount(startMessage.length)}
                    </p>
                </div>

                <!-- Feedback Received Message Input -->
                <div class="space-y-2">
                    <label
                        for="feedback-message"
                        class="mb-2 block text-start text-sm font-medium text-foreground"
                    >
                        {m.feedback_received_message()}
                    </label>
                    <Textarea
                        id="feedback-message"
                        bind:value={feedbackReceivedMessage}
                        aria-required="true"
                        required
                        class="min-h-[80px] w-full resize-none"
                        maxlength="4096"
                    />
                    <p class="text-end text-xs text-muted-foreground">
                        {formatCharacterCount(feedbackReceivedMessage.length)}
                    </p>
                </div>

                <Separator class="my-6" />

                <!-- Enable Message Confirmations Toggle -->
                <div
                    class="flex items-center justify-between rounded-lg bg-secondary/30 px-4 py-4 transition-colors hover:bg-secondary/50"
                >
                    <div class="space-y-0.5 text-start">
                        <label
                            for="enable-confirmations"
                            class="block text-sm font-medium text-foreground"
                        >
                            {m.message_confirmations()}
                        </label>
                    </div>
                    <Switch
                        id="enable-confirmations"
                        bind:checked={enableConfirmations}
                        class="ms-4 me-0 data-[state=checked]:bg-[var(--tg-theme-button-color)] data-[state=unchecked]:bg-muted-foreground/30"
                    />
                </div>

                <Separator class="my-6" />

                <!-- Save Button -->
                <div class="pt-4">
                    <Button
                        class="h-11 w-full text-base font-medium disabled:opacity-50"
                        disabled={!isFormValid || disableSubmit}
                        onclick={handleSaveBot}
                    >
                        {#if disableSubmit}
                            <Loader class="size-4 animate-spin" />
                        {:else}
                            {m.save()}
                        {/if}
                    </Button>
                </div>
            </div>
        </div>
    </Card.Root>
</div>
