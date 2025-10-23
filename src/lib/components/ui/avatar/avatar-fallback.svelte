<script>
import {Avatar as AvatarPrimitive} from 'bits-ui'
import {cn} from '~/lib/utils'

let {ref = $bindable(null), class: className, ...restProps} = $props()
</script>

<AvatarPrimitive.Fallback
    class={cn('flex size-full items-center justify-center rounded-full bg-muted', className)}
    data-slot="avatar-fallback"
    bind:ref
    {...restProps}
/>
