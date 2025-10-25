<script lang="ts">
import {Textarea} from '$lib/components/ui/textarea'
import {formatCharacterCount} from '$lib/i18n'

let {
    field_id,
    label,
    value = $bindable(''),
    required = true,
    maxlength = 4096,
    textarea_class = 'min-h-[80px] w-full resize-none',
    aria_required = undefined
} = $props<{
    field_id: string
    label: string
    value?: string
    required?: boolean
    maxlength?: number
    textarea_class?: string
    aria_required?: boolean
}>()
</script>

<section class="space-y-2">
    <label class="mb-2 block text-start text-sm font-medium text-foreground" for={field_id}>
        {label}
    </label>
    <Textarea
        id={field_id}
        class={textarea_class}
        aria-required={aria_required}
        {maxlength}
        {required}
        bind:value
    />
    <p class="text-end text-xs text-muted-foreground">
        {formatCharacterCount(value.length)}
    </p>
</section>
