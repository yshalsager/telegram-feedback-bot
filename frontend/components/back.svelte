<script lang="ts">
import {onDestroy} from 'svelte'
import {backButton, useSignal} from '@telegram-apps/sdk-svelte'

const isVisible = useSignal(backButton.isVisible)

$effect(() => {
    console.log('The button is', $isVisible ? 'visible' : 'invisible')
})

;(() => {
    try {
        backButton.mount()
        backButton.show()
    } catch (error) {
        console.error('Failed to show back button:', error)
    }
})()

onDestroy(() => {
    backButton.unmount()
    backButton.hide()
})
</script>
