<h1>Welcome to SvelteKit</h1>
<p>Visit <a href="https://svelte.dev/docs/kit">svelte.dev/docs/kit</a> to read the documentation</p>

<script lang="ts">
  import { browser } from '$app/environment';
  import { init } from '@telegram-apps/sdk-svelte';
  import { onMount } from 'svelte';

  import BackButton from '../components/back.svelte';

  let isInitialized = false;

  onMount(() => {
      init();
  });
</script>

<BackButton />