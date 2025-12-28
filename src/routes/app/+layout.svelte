<script lang="ts">
import '~/app.css'
import {csrf_token, validate_user} from '$lib/api.js'
import {initLocale} from '$lib/i18n'
import {setPageTransition} from '$lib/page_transition.js'
import {session} from '$lib/stores.svelte.js'
import {getInitData, initSDK} from '$lib/telegram.js'

type ValidationResponse = {
    status?: string
    user?: ValidatedUser
}

type ValidatedUser = {
    is_admin?: boolean
    [key: string]: unknown
}

let {children} = $props()

async function initialize() {
    await initSDK()
    const data = await getInitData()
    if (data) {
        session.update(state => ({...state, data}))
        await initLocale(data.user?.language_code)
    } else {
        await initLocale(undefined)
    }
    const csrfToken = await csrf_token()
    if (!csrfToken) {
        session.update(state => ({...state, isValid: false, isAdmin: false, user: undefined}))
        return
    }
    session.update(state => ({...state, csrfToken}))
    let validationResult: Awaited<ReturnType<typeof validate_user>> | null = null
    if (data && data.raw) {
        try {
            validationResult = await validate_user()
        } catch (error) {
            console.warn('User validation failed:', error)
            validationResult = null
        }
    }

    const validationBody = (validationResult?.data ?? null) as ValidationResponse | null
    const validatedUser = validationBody?.user
    const isValidSession = Boolean(
        data &&
        data.raw &&
        validationResult?.ok &&
        validationBody?.status === 'success' &&
        validatedUser
    )

    session.update(state => ({
        ...state,
        isValid: isValidSession,
        isAdmin: Boolean(validatedUser?.is_admin),
        user: validatedUser
    }))
}

;(async () => {
    await initialize()
})()

setPageTransition()
</script>

<svelte:head>
    <title>Feedback Bot Builder</title>
</svelte:head>

{#if $session.loaded && $session.available && $session.isValid === true}
    <div class="min-h-screen bg-background">
        <main class="container mx-auto px-4 py-6 select-none">
            {@render children?.()}
        </main>
    </div>
{/if}

{#if !$session.available}
    <div class="flex h-screen flex-col items-center justify-center">
        <h1 class="text-2xl font-bold">Please open the app in Telegram</h1>
        <p class="mt-4 text-sm text-gray-500">
            The app is not available in this browser. Please open it in Telegram.
        </p>
    </div>
{/if}

{#if $session.isValid === false}
    <div class="flex h-screen flex-col items-center justify-center">
        <h1 class="text-2xl font-bold">Invalid session</h1>
    </div>
{/if}
