<script lang="ts">
import {ChevronRight} from '@lucide/svelte'
import type {Bot, User} from '$lib/types.ts'

interface Props {
    item: Bot | User
    type: 'bot' | 'user'
    onClick: (item: Bot | User) => void
}

let {item, type, onClick}: Props = $props()

// Type guard to check if item is a Bot
function isBot(item: Bot | User): item is Bot {
    return type === 'bot'
}

// Generate avatar content based on type
const avatarContent = $derived(
    isBot(item) ? item.name.charAt(0).toUpperCase() : item.username.charAt(0).toUpperCase()
)

// Generate avatar color class based on type
const avatarClass = $derived('bg-gradient-to-br from-blue-500 to-purple-600')

// Generate secondary text based on type
const secondaryText = $derived(
    isBot(item) ? `@${item.username}${item.enabled ? '' : ' · Disabled'}` : item.telegram_id
)

const isDisabled = $derived(isBot(item) && !item.enabled)

// Generate aria label based on type
const ariaLabel = $derived(
    isBot(item) ? `Open bot ${item.name} (@${item.username})` : `Manage user @${item.username}`
)
</script>

<button
    class={`group w-full rounded-lg px-4 py-4 text-start transition-all duration-300 hover:bg-primary/30 hover:shadow-lg ${
        isDisabled ? 'opacity-70' : ''
    }`}
    aria-label={ariaLabel}
    onclick={() => onClick(item)}
>
    <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
            <!-- Avatar -->
            <div
                class="relative h-10 w-10 {avatarClass} flex items-center justify-center rounded-xl text-sm font-semibold text-white shadow-lg ring-2 ring-white/10 transition-all duration-300 group-hover:scale-110 group-hover:shadow-xl"
            >
                {avatarContent}
            </div>

            <!-- Item info -->
            <div class="space-y-1">
                <h3 class="place-self-start text-base font-semibold transition-colors" dir="auto">
                    {isBot(item) ? item.name : `@${item.username}`}
                </h3>
                <p
                    class="place-self-start text-xs text-muted-foreground transition-colors"
                    dir="auto"
                >
                    {secondaryText}
                </p>
            </div>
        </div>

        <ChevronRight
            class="h-5 w-5 text-muted-foreground transition-all duration-300 group-hover:translate-x-1 rtl:rotate-180 rtl:group-hover:translate-x-[-0.25rem]"
        />
    </div>
</button>
