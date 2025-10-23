<script>
import {Avatar as AvatarPrimitive} from 'bits-ui'
import {cn} from '~/lib/utils'

let {ref = $bindable(null), class: className, ...restProps} = $props()
</script>

<AvatarPrimitive.Image
    class={cn('aspect-square size-full', className)}
    data-slot="avatar-image"
    bind:ref
    {...restProps}
/>
