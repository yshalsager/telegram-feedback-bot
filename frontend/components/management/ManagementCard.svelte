<script lang="ts">
import type {Snippet} from 'svelte'
import * as Card from '$lib/components/ui/card/index.js'

interface Props {
    title: string
    children?: Snippet
    cta?: Snippet
    emptyState?: {
        message: string
        subMessage?: string
    }
    items?: unknown[]
}

let {title, children, cta, emptyState, items = []}: Props = $props()

const hasItems = $derived(Boolean(items.length))
</script>

<div class="space-y-2">
    <h2 class="my-3 text-lg font-medium">{title}</h2>

    <!-- List Container -->
    <Card.Root class="shadow-2xl backdrop-blur-sm">
        <Card.Content class="px-2">
            <div class="flex flex-col divide-y divide-gray-700/40">
                {#if cta}
                    <div class="py-3">
                        {@render cta()}
                    </div>
                {/if}

                {#if hasItems && children}
                    <div class="flex flex-col">
                        {@render children()}
                    </div>
                {:else if emptyState}
                    <div class="py-8 text-center text-gray-500">
                        <p class="text-base">{emptyState.message}</p>
                        {#if emptyState.subMessage}
                            <p class="mt-1 text-sm">{emptyState.subMessage}</p>
                        {/if}
                    </div>
                {/if}
            </div>
        </Card.Content>
    </Card.Root>
</div>
