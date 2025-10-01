<script lang="ts">
import {Switch} from '$lib/components/ui/switch'

type Props = {
    id: string
    label: string
    description?: string | null
    checked?: boolean
    disabled?: boolean
    containerClass?: string
    labelClass?: string
    descriptionClass?: string
    switchClass?: string
    textWrapperClass?: string
    class?: string
    [key: string]: unknown
}

let {
    id,
    label,
    description = null,
    checked = $bindable(false),
    disabled = false,
    containerClass = 'flex items-center justify-between rounded-lg bg-secondary/30 px-4 py-4 transition-colors hover:bg-secondary/50',
    labelClass = 'block text-sm font-medium text-foreground',
    descriptionClass = 'text-xs text-muted-foreground',
    switchClass = 'ms-4 me-0 data-[state=checked]:bg-[var(--tg-theme-button-color)] data-[state=unchecked]:bg-muted-foreground/30',
    textWrapperClass = 'space-y-0.5 text-start',
    ...rest
}: Props = $props()

const {class: restClass = '', ...switchRest} = rest as {
    class?: string
    [key: string]: unknown
}
</script>

<div class={containerClass}>
    <div class={textWrapperClass}>
        <label class={labelClass} for={id}>
            {label}
        </label>
        {#if description}
            <p class={descriptionClass}>{description}</p>
        {/if}
    </div>
    <Switch
        {id}
        class={`${switchClass}${restClass ? ` ${restClass}` : ''}`}
        {disabled}
        bind:checked
        {...switchRest}
    />
</div>
