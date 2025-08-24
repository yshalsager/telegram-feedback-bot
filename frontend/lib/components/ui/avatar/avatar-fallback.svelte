<script>
import {Avatar as AvatarPrimitive} from 'bits-ui'
import {cn} from '$lib/utils.js'

let {ref = $bindable(null), class: className, ...restProps} = $props()
</script>

<AvatarPrimitive.Fallback
    bind:ref
    data-slot="avatar-fallback"
    class={cn('flex size-full items-center justify-center rounded-full bg-muted', className)}
    {...restProps}
/>
