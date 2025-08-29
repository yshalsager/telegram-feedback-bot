<script lang="ts">
import '../app.css'
import {session} from '$lib/stores.svelte.js'
import {getInitData, initSDK} from '$lib/telegram.js'
import {m} from '$lib/paraglide/messages.js'
import {csrf_token, validate_user} from '$lib/api.js'
import Navbar from '~/components/navbar.svelte'

let {children} = $props()

async function initialize() {
    await initSDK()
    const data = await getInitData()
    if (data) session.update(state => ({...state, data}))
    const csrfToken = await csrf_token()
    session.update(state => ({...state, csrfToken}))
    const isValidSession = data && data.raw && (await validate_user())
    session.update(state => ({...state, isValid: isValidSession || false}))
}

;(async () => {
    await initialize()
})()
</script>

<svelte:head>
    <title>{m.app_name()}</title>
</svelte:head>

{#if $session.loaded && $session.available && $session.isValid === true}
    <div class="min-h-screen bg-background">
        <Navbar />
        <main class="container mx-auto px-4 py-6">
            {@render children?.()}
        </main>
    </div>
{/if}

{#if !$session.available}
    <div class="flex h-screen flex-col items-center justify-center">
        <h1 class="text-2xl font-bold">{m.please_open_in_telegram()}</h1>
        <p class="mt-4 text-sm text-gray-500">
            {m.the_app_is_not_available_in_this_browser()}
        </p>
    </div>
{/if}

{#if $session.isValid === false}
    <div class="flex h-screen flex-col items-center justify-center">
        <h1 class="text-2xl font-bold">{m.invalid_session()}</h1>
    </div>
{/if}
