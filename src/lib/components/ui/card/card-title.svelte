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
    class={cn('leading-none font-semibold', className)}
    data-slot="card-title"
    {...restProps}
>
    {@render children?.()}
</div>
