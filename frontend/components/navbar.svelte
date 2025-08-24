<script>
// @ts-nocheck

import {session} from '$lib/stores.svelte.js'
import * as Avatar from '$lib/components/ui/avatar/index.js'
import * as Popover from '$lib/components/ui/popover/index.js'
import {User, Hash, Globe} from '@lucide/svelte/icons'
import {m} from '$lib/paraglide/messages.js'

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

<nav class="bg-background-800 border-b border-primary px-4 py-2.5">
    <div class="mx-auto flex max-w-screen-xl flex-wrap items-center justify-between">
        <div class="flex items-center">
            <span class="text-xl font-semibold text-primary select-none">{m.app_name()}</span>
        </div>

        <!-- User Menu -->
        <div class="flex items-center space-x-3">
            <div class="flex items-center space-x-2">
                <span class="hidden text-sm text-gray-600 md:block">
                    {$session.data?.user?.first_name || ''}
                    {$session.data?.user?.last_name || ''}
                    {#if $session.data?.user?.username}
                        <span class="text-gray-400">(@{$session.data?.user?.username})</span>
                    {/if}
                </span>

                <!-- Avatar with Popover -->
                <Popover.Root>
                    <Popover.Trigger class="">
                        <!-- eslint-disable-next-line no-explicit-any -->
                        {#snippet child({props})}
                            <Avatar.Root
                                class="h-8 w-8 cursor-pointer transition-all hover:ring-2 hover:ring-primary/50"
                                {...props}
                            >
                                {#if $session.data?.user?.photo_url}
                                    <Avatar.Image
                                        src={$session.data.user.photo_url}
                                        alt={m.profile_picture()}
                                        class=""
                                    />
                                {/if}
                                <Avatar.Fallback class="bg-primary text-xs text-primary-foreground">
                                    {getUserInitials(
                                        $session.data?.user?.first_name || '',
                                        $session.data?.user?.last_name || '',
                                        $session.data?.user?.username || ''
                                    )}
                                </Avatar.Fallback>
                            </Avatar.Root>
                        {/snippet}
                    </Popover.Trigger>
                    <Popover.Content
                        class="w-80 bg-background"
                        align="end"
                        side="bottom"
                        portalProps={{}}
                    >
                        <div class="space-y-4">
                            <!-- User Info Header -->
                            <div class="flex items-start space-x-3">
                                <div class="flex-shrink-0 pt-0.5">
                                    <User class="h-4 w-4 text-muted-foreground" />
                                </div>
                                <div class="min-w-0 flex-1">
                                    <h4 class="leading-tight font-semibold text-foreground">
                                        {$session.data?.user?.first_name || ''}
                                        {$session.data?.user?.last_name || ''}
                                    </h4>
                                    {#if $session.data?.user?.username}
                                        <p class="text-sm leading-tight text-muted-foreground">
                                            @{$session.data?.user?.username}
                                        </p>
                                    {/if}
                                </div>
                            </div>

                            <!-- User Details -->
                            <div class="space-y-3">
                                <!-- User ID -->
                                <div class="flex items-start space-x-3">
                                    <div class="flex-shrink-0 pt-0.5">
                                        <Hash class="h-4 w-4 text-muted-foreground" />
                                    </div>
                                    <div class="min-w-0 flex-1">
                                        <p
                                            class="text-sm leading-tight font-medium text-foreground"
                                        >
                                            {m.user_id()}
                                        </p>
                                        <p
                                            class="font-mono text-xs leading-tight break-all text-muted-foreground"
                                        >
                                            {$session.data?.user?.id || 'N/A'}
                                        </p>
                                    </div>
                                </div>

                                <!-- Language -->
                                <div class="flex items-start space-x-3">
                                    <div class="flex-shrink-0 pt-0.5">
                                        <Globe class="h-4 w-4 text-muted-foreground" />
                                    </div>
                                    <div class="min-w-0 flex-1">
                                        <p
                                            class="text-sm leading-tight font-medium text-foreground"
                                        >
                                            {m.language()}
                                        </p>
                                        <p class="text-xs leading-tight text-muted-foreground">
                                            {$session.data?.user?.language_code || m.unknown()}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Popover.Content>
                </Popover.Root>
            </div>
        </div>
    </div>
</nav>
