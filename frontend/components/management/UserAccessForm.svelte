<script lang="ts">
import type {Snippet} from 'svelte'
import {Loader} from '@lucide/svelte'
import {Button} from '$lib/components/ui/button'
import {Input} from '$lib/components/ui/input'
import {Separator} from '$lib/components/ui/separator/index.js'
import {availableLocales} from '$lib/i18n'
import SwitchRow from './SwitchRow.svelte'

type Props = {
    username?: string
    languageCode?: string
    isWhitelisted?: boolean
    isAdmin?: boolean
    submitLabel?: string
    submitDisabled?: boolean
    isSubmitting?: boolean
    usernameLabel?: string
    languageLabel?: string
    whitelistLabel?: string
    whitelistDescription?: string
    adminLabel?: string
    adminDescription?: string
    onsubmit?: () => void
    showSubmitButton?: boolean
}

let {
    username = $bindable(''),
    languageCode = $bindable(''),
    isWhitelisted = $bindable(true),
    isAdmin = $bindable(false),
    submitLabel = 'Save',
    submitDisabled = false,
    isSubmitting = false,
    usernameLabel = 'Username',
    languageLabel = 'Language',
    whitelistLabel = 'Whitelist access',
    whitelistDescription = 'Allows the user to open the builder mini app.',
    adminLabel = 'Admin access',
    adminDescription = 'Grants builder admin permissions to this user.',
    onsubmit,
    before,
    showSubmitButton = true
}: Props & {
    before?: Snippet
} = $props()

function handleSubmit() {
    if (!submitDisabled) {
        onsubmit?.()
    }
}
</script>

<div class="space-y-6">
    {#if before}
        {@render before()}
    {/if}

    <div class="space-y-2">
        <label class="mb-2 block text-start text-sm font-medium text-foreground" for="username">
            {usernameLabel}
        </label>
        <Input
            id="username"
            class="w-full"
            aria-required="false"
            dir="ltr"
            placeholder="username"
            type="text"
            bind:value={username}
        />
        <p class="text-start text-xs text-muted-foreground">
            Optional. Enter the Telegram username without the @ symbol.
        </p>
    </div>

    <Separator class="my-6" />

    <div class="space-y-2">
        <label class="mb-2 block text-start text-sm font-medium text-foreground" for="language">
            {languageLabel}
        </label>
        <select
            id="language"
            class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
            bind:value={languageCode}
        >
            {#each $availableLocales as locale (locale.locale)}
                <option value={locale.locale}>{locale.name}</option>
            {/each}
        </select>
    </div>

    <Separator class="my-6" />

    <SwitchRow
        id="whitelisted"
        description={whitelistDescription}
        label={whitelistLabel}
        bind:checked={isWhitelisted}
    />

    <SwitchRow
        id="is-admin"
        description={adminDescription}
        label={adminLabel}
        bind:checked={isAdmin}
    />

    {#if showSubmitButton}
        <Separator class="my-6" />

        <div class="pt-4">
            <Button
                class="h-11 w-full text-base font-medium disabled:opacity-50"
                disabled={submitDisabled}
                onclick={handleSubmit}
            >
                {#if isSubmitting}
                    <Loader class="size-4 animate-spin" />
                {:else}
                    {submitLabel}
                {/if}
            </Button>
        </div>
    {/if}
</div>
