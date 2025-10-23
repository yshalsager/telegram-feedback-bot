<script lang="ts">
import {goto} from '$app/navigation'
import {resolve} from '$app/paths'
import {Plus, UserPlus} from '@lucide/svelte'
import {cn} from '$lib/utils.js'

type IconVariant = 'plus' | 'user-plus'
type GradientVariant = 'primary' | 'success'

const ICONS = {
    plus: Plus,
    'user-plus': UserPlus
} satisfies Record<IconVariant, typeof Plus>

const GRADIENTS = {
    primary: {
        hover: 'hover:bg-gradient-to-r hover:from-blue-600/20 hover:to-purple-600/20',
        overlay: {
            direction: 'bg-gradient-to-r',
            colors: 'from-blue-600/10 to-purple-600/10'
        },
        icon: {
            direction: 'bg-gradient-to-br',
            colors: 'from-blue-600 to-purple-600'
        }
    },
    success: {
        hover: 'hover:bg-gradient-to-r hover:from-green-600/20 hover:to-emerald-600/20',
        overlay: {
            direction: 'bg-gradient-to-r',
            colors: 'from-green-600/10 to-emerald-600/10'
        },
        icon: {
            direction: 'bg-gradient-to-br',
            colors: 'from-green-600 to-emerald-600'
        }
    }
} satisfies Record<
    GradientVariant,
    {
        hover: string
        overlay: {direction: string; colors: string}
        icon: {direction: string; colors: string}
    }
>

type RouteTarget = Parameters<typeof resolve>[0]

interface Props {
    label: string
    icon?: IconVariant
    variant?: GradientVariant
    onClick?: () => void
    route?: RouteTarget
}

let {label, icon = 'plus', variant = 'primary', onClick, route}: Props = $props()

const Icon = $derived(ICONS[icon])
const gradient = $derived(GRADIENTS[variant] ?? GRADIENTS.primary)

function handleClick() {
    if (route) {
        goto(resolve(route))
        return
    }
    onClick?.()
}
</script>

<button
    class={cn(
        'group relative flex w-full items-center gap-4 rounded-lg px-4 py-5 text-start transition-all duration-300 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary/40',
        gradient.hover
    )}
    aria-label={label}
    onclick={handleClick}
>
    <!-- Background gradient effect -->
    <div
        class={cn(
            'pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100',
            gradient.overlay.direction,
            gradient.overlay.colors
        )}
    ></div>

    <div
        class={cn(
            'relative flex h-12 w-12 items-center justify-center rounded-2xl shadow-lg transition-all duration-300 group-hover:scale-110 group-hover:shadow-xl',
            gradient.icon.direction,
            gradient.icon.colors
        )}
    >
        <Icon class="h-6 w-6 text-white" />
    </div>
    <div class="relative space-y-1">
        <span class="text-lg font-semibold text-primary">{label}</span>
    </div>
</button>
