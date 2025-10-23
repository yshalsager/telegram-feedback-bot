<script>
import {cn} from '~/lib/utils'

let {ref = $bindable(null), class: className, children, ...restProps} = $props()
</script>

<p
    bind:this={ref}
    class={cn('text-sm text-muted-foreground', className)}
    data-slot="card-description"
    {...restProps}
>
    {@render children?.()}
</p>
