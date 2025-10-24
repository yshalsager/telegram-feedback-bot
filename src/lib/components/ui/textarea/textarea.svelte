<script lang="ts">
import type {HTMLTextareaAttributes} from 'svelte/elements'
import {cn, type WithElementRef, type WithoutChildren} from '~/lib/utils'

let {
    ref = $bindable(null),
    value = $bindable(),
    class: className,
    'data-slot': dataSlot = 'textarea',
    ...restProps
}: WithoutChildren<WithElementRef<HTMLTextareaAttributes>> = $props()
</script>

<textarea
    bind:this={ref}
    class={cn(
        'flex field-sizing-content min-h-16 w-full rounded-md border border-input bg-transparent px-3 py-2 text-base shadow-xs transition-[color,box-shadow] outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-destructive/20 md:text-sm dark:bg-input/30 dark:aria-invalid:ring-destructive/40',
        className
    )}
    data-slot={dataSlot}
    bind:value
    {...restProps}
></textarea>
