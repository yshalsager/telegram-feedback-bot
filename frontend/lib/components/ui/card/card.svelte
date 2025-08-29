<script>
import {cn} from '$lib/utils.js'

let {ref = $bindable(null), class: className, children, ...restProps} = $props()
</script>

<div
    bind:this={ref}
    data-slot="card"
    class={cn(
        'flex flex-col gap-6 rounded-xl border bg-card py-6 text-card-foreground shadow-sm',
        className
    )}
    {...restProps}
>
    {@render children?.()}
</div>
