<script>
import {cn} from '~/lib/utils'

let {ref = $bindable(null), class: className, children, ...restProps} = $props()
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
