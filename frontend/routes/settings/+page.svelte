<script lang="ts">
import {Globe, Hash} from '@lucide/svelte/icons'
import {set_language} from '$lib/api.js'
import * as Avatar from '$lib/components/ui/avatar/index.js'
import * as Card from '$lib/components/ui/card/index.js'
import {Separator} from '$lib/components/ui/separator/index.js'
import {applyLocale, availableLocales, locale} from '$lib/i18n'
import {session} from '$lib/stores.svelte.js'
import {showNotification} from '$lib/telegram.js'

function getUserInitials(firstName: string, lastName: string, username: string) {
    if (firstName && lastName) {
        return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase()
    }
    if (firstName) {
        return firstName.charAt(0).toUpperCase()
    }
    if (username) {
        return username.charAt(0).toUpperCase()
    }
    return 'U'
}

async function handleLanguageSelect(code: string) {
    if (code === $locale) return

    const updated = await set_language(code)
    if (updated) {
        await applyLocale(code)
        session.update(state => {
            const current = state.data
            if (!current?.user) return state

            return {
                ...state,
                data: {
                    ...current,
                    user: {...current.user, language_code: code}
                }
            }
        })
        return
    }

    showNotification('Failed to set language', 'Please try again later', [
        {id: 'language_error_close', type: 'close'}
    ])
}
</script>

<div class="mx-auto min-h-screen max-w-lg">
    <!-- User Profile Card -->
    <Card.Root class="mb-6 shadow-2xl backdrop-blur-sm">
        <div class="p-6">
            <div class="flex items-center gap-4">
                {#if $session.data?.user?.photo_url}
                    <Avatar.Root class="h-16 w-16">
                        <Avatar.Image
                            class="h-16 w-16"
                            alt="Profile Picture"
                            src={$session.data.user.photo_url}
                        />
                        <Avatar.Fallback class="bg-primary text-primary-foreground">
                            {getUserInitials(
                                $session.data?.user?.first_name || '',
                                $session.data?.user?.last_name || '',
                                $session.data?.user?.username || ''
                            )}
                        </Avatar.Fallback>
                    </Avatar.Root>
                {:else}
                    <Avatar.Root class="h-16 w-16">
                        <Avatar.Fallback class="bg-primary text-primary-foreground">
                            {getUserInitials(
                                $session.data?.user?.first_name || '',
                                $session.data?.user?.last_name || '',
                                $session.data?.user?.username || ''
                            )}
                        </Avatar.Fallback>
                    </Avatar.Root>
                {/if}
                <div class="flex-1">
                    <h1 class="text-xl font-bold">
                        {$session.data?.user?.first_name || ''}
                        {$session.data?.user?.last_name || ''}
                    </h1>
                    {#if $session.data?.user?.username}
                        <p class="text-sm text-muted-foreground">
                            @{$session.data?.user?.username}
                        </p>
                    {/if}
                </div>
            </div>
        </div>

        <Separator class="" />

        <Card.Content class="space-y-4">
            <div class="flex items-start gap-3">
                <Hash class="mt-0.5 h-4 w-4 text-muted-foreground" />
                <div class="flex-1">
                    <p class="text-sm font-medium">User ID</p>
                    <p class="font-mono text-xs break-all text-muted-foreground">
                        {$session.data?.user?.id || 'N/A'}
                    </p>
                </div>
            </div>
            <div class="flex items-start gap-3">
                <Globe class="mt-0.5 h-4 w-4 text-muted-foreground" />
                <div class="flex-1">
                    <p class="text-sm font-medium">Language</p>
                    <p class="text-xs text-muted-foreground">
                        {$session.data?.user?.language_code || 'Unknown'}
                    </p>
                </div>
            </div>
        </Card.Content>
    </Card.Root>

    <!-- Language Settings Card -->
    <Card.Root class="shadow-2xl backdrop-blur-sm">
        <Card.Header class="">
            <Card.Title class="">Language</Card.Title>
        </Card.Header>
        <Card.Content class="">
            <div class="space-y-2">
                {#each $availableLocales as option (option.locale)}
                    <button
                        class="group flex w-full items-center justify-between rounded-lg p-3 transition-all duration-300 hover:bg-primary/50 {option.locale ===
                        $locale
                            ? 'bg-primary/25'
                            : ''}"
                        onclick={() => handleLanguageSelect(option.locale)}
                    >
                        <span class="font-medium">{option.name}</span>
                        {#if option.locale === $locale}
                            <div class="h-2 w-2 rounded-full bg-primary"></div>
                        {/if}
                    </button>
                {/each}
            </div>
        </Card.Content>
    </Card.Root>
</div>
