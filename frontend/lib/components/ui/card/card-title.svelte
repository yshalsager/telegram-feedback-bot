<script>
import {cn} from '~/lib/utils'

let {ref = $bindable(null), class: className, children, ...restProps} = $props()
</script>

<div
    bind:this={ref}
    class={cn('leading-none font-semibold', className)}
    data-slot="card-title"
    {...restProps}
>
    {@render children?.()}
</div>
