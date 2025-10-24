<script lang="ts">
import {Popover as PopoverPrimitive} from 'bits-ui'
import {cn} from '~/lib/utils'

let {
    ref = $bindable(null),
    class: className,
    ...restProps
}: PopoverPrimitive.TriggerProps = $props()
</script>

<PopoverPrimitive.Trigger
    class={cn('', className)}
    data-slot="popover-trigger"
    bind:ref
    {...restProps}
/>
