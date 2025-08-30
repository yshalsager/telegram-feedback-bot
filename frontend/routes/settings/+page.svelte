<script>
import {set_language} from '$lib/api.js'
import * as Avatar from '$lib/components/ui/avatar/index.js'
import * as Card from '$lib/components/ui/card/index.js'
import {Separator} from '$lib/components/ui/separator/index.js'
import {m} from '$lib/paraglide/messages.js'
import {getLocale, locales, setLocale} from '$lib/paraglide/runtime.js'
import {session} from '$lib/stores.svelte.js'
import {showNotification} from '$lib/telegram.js'
import {Globe, Hash} from '@lucide/svelte/icons'

let currentLocale = $state(getLocale())
const languageNameFormatter = new Intl.DisplayNames([currentLocale], {type: 'language'})
const availableLanguages = locales.map(locale => ({
    locale,
    name: languageNameFormatter.of(locale)
}))

/**
 * Returns the user's initials based on their first name, last name, or username.
 *
 * @param {string} firstName - The user's first name.
 * @param {string} lastName - The user's last name.
 * @param {string} username - The user's username.
 * @returns {string} The initials to display for the user.
 */
function getUserInitials(firstName, lastName, username) {
    if (firstName && lastName) {
        return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase()
    } else if (firstName) {
        return firstName.charAt(0).toUpperCase()
    } else if (username) {
        return username.charAt(0).toUpperCase()
    }
    return 'U'
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
                            src={$session.data.user.photo_url}
                            alt={m.profile_picture()}
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
                    <p class="text-sm font-medium">{m.user_id()}</p>
                    <p class="font-mono text-xs break-all text-muted-foreground">
                        {$session.data?.user?.id || 'N/A'}
                    </p>
                </div>
            </div>
            <div class="flex items-start gap-3">
                <Globe class="mt-0.5 h-4 w-4 text-muted-foreground" />
                <div class="flex-1">
                    <p class="text-sm font-medium">{m.language()}</p>
                    <p class="text-xs text-muted-foreground">
                        {$session.data?.user?.language_code || m.unknown()}
                    </p>
                </div>
            </div>
        </Card.Content>
    </Card.Root>

    <!-- Language Settings Card -->
    <Card.Root class="shadow-2xl backdrop-blur-sm">
        <Card.Header class="">
            <Card.Title class="">{m.language()}</Card.Title>
        </Card.Header>
        <Card.Content class="">
            <div class="space-y-2">
                {#each availableLanguages as locale (locale.locale)}
                    <button
                        class="group flex w-full items-center justify-between rounded-lg p-3 transition-all duration-300 hover:bg-primary/50 {locale.locale ===
                        currentLocale
                            ? 'bg-primary/25'
                            : ''}"
                        onclick={async () => {
                            if (await set_language(locale.locale)) {
                                setLocale(locale.locale)
                            } else {
                                showNotification(
                                    m.failed_to_set_language(),
                                    m.please_try_again_later(),
                                    [{id: 'language_error_close', type: 'close'}]
                                )
                            }
                        }}
                    >
                        <span class="font-medium">{locale.name}</span>
                        {#if locale.locale === currentLocale}
                            <div class="h-2 w-2 rounded-full bg-primary"></div>
                        {/if}
                    </button>
                {/each}
            </div>
        </Card.Content>
    </Card.Root>
</div>
