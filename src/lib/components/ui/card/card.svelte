<script lang="ts">
import type {HTMLAttributes} from 'svelte/elements'
import {cn, type WithElementRef} from '~/lib/utils'

let {
    ref = $bindable(null),
    class: className,
    children,
    ...restProps
}: WithElementRef<HTMLAttributes<HTMLDivElement>> = $props()
</script>

<div
    bind:this={ref}
    class={cn(
        'flex flex-col gap-6 rounded-xl border bg-card py-6 text-card-foreground shadow-sm',
        className
    )}
    data-slot="card"
    {...restProps}
>
    {@render children?.()}
</div>
