<script>
import {cn} from '~/lib/utils'

let {ref = $bindable(null), class: className, children, ...restProps} = $props()
</script>

<div
    bind:this={ref}
    class={cn('flex items-center px-6 [.border-t]:pt-6', className)}
    data-slot="card-footer"
    {...restProps}
>
    {@render children?.()}
</div>
