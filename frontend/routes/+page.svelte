<script lang="ts">
import BackButton from '../components/back.svelte'
import {m} from '$lib/paraglide/messages.js'
import {session} from '$lib/stores.svelte.js'
</script>

<h1>{m.app_name()}</h1>

<p>
    Welcome, {$session.data?.user?.first_name}
    {$session.data?.user?.last_name || ''} (@{$session.data?.user?.username})
</p>
<p>Your User ID: {$session.data?.user?.id}</p>
<p>Your Language: {$session.data?.user?.language_code}</p>

<BackButton />
