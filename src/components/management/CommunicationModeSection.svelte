<script lang="ts">
import type {CommunicationMode} from '$lib/constants/communication_mode'
import {communication_mode_options} from '$lib/constants/communication_mode'

let {
    value = $bindable<CommunicationMode>('standard'),
    heading = 'Communication mode',
    options = communication_mode_options
} = $props<{
    value?: CommunicationMode
    heading?: string
    options?: typeof communication_mode_options
}>()
</script>

<section class="space-y-2">
    <span class="block text-start text-sm font-semibold text-foreground">{heading}</span>
    <div class="space-y-2">
        {#each options as option (option.value)}
            <label
                class="flex cursor-pointer items-start gap-3 rounded-lg border border-border bg-background px-3 py-2 text-sm"
            >
                <input
                    name="communication-mode"
                    class="mt-1 accent-[var(--tg-theme-button-color)]"
                    checked={value === option.value}
                    onchange={() => (value = option.value)}
                    type="radio"
                    value={option.value}
                />
                <span class="space-y-1">
                    <span class="block font-medium text-foreground">{option.title}</span>
                    <span class="block text-xs text-muted-foreground">{option.description}</span>
                </span>
            </label>
        {/each}
    </div>
</section>
