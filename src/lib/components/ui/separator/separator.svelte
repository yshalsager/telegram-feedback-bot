<script>
import {Separator as SeparatorPrimitive} from 'bits-ui'
import {cn} from '~/lib/utils'

let {ref = $bindable(null), class: className, ...restProps} = $props()
</script>

<SeparatorPrimitive.Root
    class={cn(
        'shrink-0 bg-border data-[orientation=horizontal]:h-px data-[orientation=horizontal]:w-full data-[orientation=vertical]:h-full data-[orientation=vertical]:w-px',
        className
    )}
    data-slot="separator"
    bind:ref
    {...restProps}
/>
