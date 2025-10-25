<script lang="ts">
import {goto} from '$app/navigation'
import {resolve} from '$app/paths'
import {Loader} from '@lucide/svelte'
import type {EventPayload} from '@telegram-apps/sdk-svelte'
import {on} from '@telegram-apps/sdk-svelte'
import SettingsPage from '~/components/management/SettingsPage.svelte'
import {showNotification} from '~/lib/telegram.js'
import {add_bot} from '$lib/api.js'
import {Button} from '$lib/components/ui/button'
import {Input} from '$lib/components/ui/input'
import {Separator} from '$lib/components/ui/separator'
import {Textarea} from '$lib/components/ui/textarea'
import {formatCharacterCount} from '$lib/i18n'

type AddBotResponse = {
    status?: string
    message?: unknown
    bot?: {
        username?: string | null
    } | null
}

let botToken = $state('')
let startMessage = $state(/* @wc-include */ 'Welcome to [name] bot. Please send your feedback.')
let feedbackReceivedMessage = $state(
    /* @wc-include */ 'Thank you for your feedback. We will get back to you soon.'
)
let communication_mode = $state('standard')
let disableSubmit = $state(false)
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

const communication_mode_options: {
    value: 'standard' | 'private' | 'anonymous'
    title: string
    description: string
}[] = [
    {
        value: 'standard',
        title: 'Standard',
        description: 'Forward with usernames and profile links.'
    },
    {
        value: 'private',
        title: 'Private',
        description: 'Shows public name only; profile links removed.'
    },
    {
        value: 'anonymous',
        title: 'Anonymous',
        description: 'Replaces user identity with a request number.'
    }
]

// Format character count with locale-specific number formatting
const onBotSuccessfullyAdded = on('popup_closed', (payload: EventPayload<'popup_closed'>) => {
    if (payload.button_id === 'bot_successfully_added_close') goto(resolve('/app'))
    onBotSuccessfullyAdded()
})

async function handleSaveBot() {
    disableSubmit = true
    const response = (await add_bot(
        botToken,
        startMessage,
        feedbackReceivedMessage,
        communication_mode
    )) as AddBotResponse
    if (response?.status === 'success') {
        showNotification(
            '',
            `Successfully added @${response.bot?.username || ''} to your bots list. Please add to a group to work better.`,
            [{id: 'bot_successfully_added_close', type: 'close'}]
        )
    } else {
        const message =
            response && response.message ? String(response.message) : 'Failed to add bot'
        showNotification('', `❗ ${message}`, [{id: 'bot_failed_to_add_close', type: 'close'}])
    }
    disableSubmit = false
}
</script>

<SettingsPage ariaLabel="Adding Bot interface" dir="auto" title="Add new bot">
    <div class="space-y-6">
        <section class="space-y-2">
            <label
                class="mb-2 block text-start text-sm font-medium text-foreground"
                for="bot-token"
            >
                Bot token
            </label>
            <Input
                id="bot-token"
                class={`w-full ${!isTokenValid ? 'border-destructive focus-visible:ring-destructive/20' : ''}`}
                aria-describedby={!isTokenValid ? 'token-error' : undefined}
                aria-invalid={!isTokenValid}
                aria-required="true"
                dir="ltr"
                placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz123456789"
                required
                type="text"
                bind:value={botToken}
            />
            {#if !isTokenValid}
                <p id="token-error" class="text-start text-sm text-destructive" role="alert">
                    Bot token must be in format: numbers:letters (8-10 digits : 35 characters)
                </p>
            {/if}
        </section>

        <Separator class="my-6" />

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
                aria-required="true"
                maxlength={4096}
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
                aria-required="true"
                maxlength={4096}
                required
                bind:value={feedbackReceivedMessage}
            />
            <p class="text-end text-xs text-muted-foreground">
                {formatCharacterCount(feedbackReceivedMessage.length)}
            </p>
        </section>

        <section class="space-y-2">
            <span class="block text-start text-sm font-semibold text-foreground">
                Communication mode
            </span>
            <div class="space-y-2">
                {#each communication_mode_options as option (option.value)}
                    <label
                        class="flex cursor-pointer items-start gap-3 rounded-lg border border-border bg-background px-3 py-2 text-sm"
                    >
                        <input
                            name="communication-mode"
                            class="mt-1 accent-[var(--tg-theme-button-color)]"
                            checked={communication_mode === option.value}
                            onchange={() => (communication_mode = option.value)}
                            type="radio"
                            value={option.value}
                        />
                        <span class="space-y-1">
                            <span class="block font-medium text-foreground">{option.title}</span>
                            <span class="block text-xs text-muted-foreground"
                                >{option.description}</span
                            >
                        </span>
                    </label>
                {/each}
            </div>
        </section>

        <div class="pt-4">
            <Button
                class="h-11 w-full text-base font-medium disabled:opacity-50"
                disabled={!isFormValid || disableSubmit}
                onclick={handleSaveBot}
            >
                {#if disableSubmit}
                    <Loader class="size-4 animate-spin" />
                {:else}
                    Save
                {/if}
            </Button>
        </div>
    </div>
</SettingsPage>
