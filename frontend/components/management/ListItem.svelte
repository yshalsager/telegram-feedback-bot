<script lang="ts">
import {ChevronRight} from '@lucide/svelte'
import type {Bot, User} from '$lib/types.ts'

interface Props {
    item: Bot | User
    type: 'bot' | 'user'
    onClick: (item: Bot | User) => void
}

let {item, type, onClick}: Props = $props()

const avatarPalette = [
    'bg-gradient-to-br from-blue-500 to-purple-600',
    'bg-gradient-to-br from-emerald-500 to-teal-600',
    'bg-gradient-to-br from-amber-500 to-orange-600',
    'bg-gradient-to-br from-rose-500 to-pink-600',
    'bg-gradient-to-br from-indigo-500 to-sky-600',
    'bg-gradient-to-br from-slate-500 to-slate-700',
    'bg-gradient-to-br from-lime-500 to-green-600',
    'bg-gradient-to-br from-cyan-500 to-sky-500',
    'bg-gradient-to-br from-fuchsia-500 to-purple-700',
    'bg-gradient-to-br from-red-500 to-orange-700',
    'bg-gradient-to-br from-violet-500 to-indigo-700',
    'bg-gradient-to-br from-stone-500 to-stone-700'
]

function hashColorKey(value: string): number {
    let hash = 5381
    for (let i = 0; i < value.length; i += 1) {
        hash = ((hash << 5) + hash) ^ value.charCodeAt(i)
    }
    return Math.abs(hash)
}

function pickAvatarClass(value: string): string {
    if (!value) return avatarPalette[0]
    const hashed = hashColorKey(value)
    return avatarPalette[hashed % avatarPalette.length]
}

// Type guard to check if item is a Bot
function isBot(item: Bot | User): item is Bot {
    return type === 'bot'
}

// Generate avatar content based on type
const avatarContent = $derived(
    isBot(item) ? item.name.charAt(0).toUpperCase() : (item.username?.charAt(0).toUpperCase() ?? '')
)

// Generate avatar color class based on type
const avatarClass = $derived(
    pickAvatarClass(
        isBot(item) ? (item.uuid ?? String(item.telegram_id)) : String(item.telegram_id)
    )
)

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
