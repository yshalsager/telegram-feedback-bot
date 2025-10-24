<script lang="ts">
import type {Snippet} from 'svelte'
import * as Card from '$lib/components/ui/card'

type Props = {
    title: string
    subtitle?: string | null
    ariaLabel?: string | null
    role?: string
    dir?: 'ltr' | 'rtl' | 'auto'
    containerClass?: string
    headerClass?: string
    titleClass?: string
    subtitleClass?: string
    cardClass?: string
    contentClass?: string
}

let {
    title,
    subtitle = null,
    ariaLabel = null,
    role = 'application',
    dir = 'auto',
    containerClass = 'mx-auto min-h-screen max-w-lg py-8',
    headerClass = 'mb-8 space-y-2 text-center',
    titleClass = 'text-xl font-bold sm:text-2xl md:text-3xl lg:text-4xl xl:text-5xl',
    subtitleClass = 'text-sm text-muted-foreground',
    cardClass = 'mb-6 shadow-2xl backdrop-blur-sm',
    contentClass = 'p-6 space-y-6',
    header,
    children,
    footer
}: Props & {
    header?: Snippet
    children?: Snippet
    footer?: Snippet
} = $props()
</script>

{#snippet defaultHeader()}
    <h2 class={titleClass}>{title}</h2>
    {#if subtitle}
        <p class={subtitleClass}>{subtitle}</p>
    {/if}
{/snippet}

<div class={containerClass} aria-label={ariaLabel ?? undefined} {dir} {role}>
    <div class={headerClass}>
        {#if header}
            {@render header()}
        {:else}
            {@render defaultHeader()}
        {/if}
    </div>

    <Card.Root class={cardClass}>
        <div class={contentClass}>
            {#if children}
                {@render children()}
            {/if}
        </div>
    </Card.Root>

    {#if footer}
        {@render footer()}
    {/if}
</div>
