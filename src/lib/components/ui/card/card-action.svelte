<script>
import {cn} from '~/lib/utils'

let {ref = $bindable(null), class: className, children, ...restProps} = $props()
</script>

<div
    bind:this={ref}
    class={cn('col-start-2 row-span-2 row-start-1 self-start justify-self-end', className)}
    data-slot="card-action"
    {...restProps}
>
    {@render children?.()}
</div>
