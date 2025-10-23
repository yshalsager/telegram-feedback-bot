<script>
import {cn} from '~/lib/utils'

let {ref = $bindable(null), class: className, children, ...restProps} = $props()
</script>

<div bind:this={ref} class={cn('px-6', className)} data-slot="card-content" {...restProps}>
    {@render children?.()}
</div>
