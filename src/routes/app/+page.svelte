<script lang="ts">
import {goto} from '$app/navigation'
import {resolve} from '$app/paths'
import {onMount} from 'svelte'
import {Search} from '@lucide/svelte'
import AddButton from '~/components/management/AddButton.svelte'
import ListItem from '~/components/management/ListItem.svelte'
import ManagementCard from '~/components/management/ManagementCard.svelte'
import {list_bots, list_users} from '$lib/api.js'
import {Input} from '$lib/components/ui/input'
import {Separator} from '$lib/components/ui/separator'
import {session} from '$lib/stores.svelte.js'
import type {Bot, User} from '$lib/types.ts'

let searchQuery = $state('')
let bots = $state<Bot[]>([])
let users = $state<User[]>([])

const trimmedQuery = $derived(searchQuery.trim())
const normalizedQuery = $derived(trimmedQuery.toLowerCase())

let botsLoaded = false
let usersLoaded = false

async function loadBots() {
    try {
        const botsRaw = await list_bots()
        bots = (botsRaw as Bot[]) || []
    } catch (error) {
        console.error('Failed to load bots:', error)
        bots = []
        botsLoaded = false
    }
}

async function loadUsers() {
    try {
        const usersRaw = await list_users()
        users = (usersRaw as User[]) || []
    } catch (error) {
        console.error('Failed to load users:', error)
        users = []
        usersLoaded = false
    }
}

onMount(() => {
    const unsubscribe = session.subscribe(async value => {
        if (!value.loaded || !value.isValid || !value.csrfToken) {
            bots = []
            users = []
            botsLoaded = false
            usersLoaded = false
            return
        }

        if (!botsLoaded) {
            botsLoaded = true
            await loadBots()
        }

        if (value.isAdmin) {
            if (!usersLoaded) {
                usersLoaded = true
                await loadUsers()
            }
        } else {
            users = []
            usersLoaded = false
        }
    })

    return () => {
        unsubscribe()
    }
})

const filteredBots = $derived(
    bots.filter(bot =>
        !trimmedQuery
            ? true
            : bot.name.toLowerCase().includes(normalizedQuery) ||
              bot.username.toLowerCase().includes(normalizedQuery)
    )
)

const filteredUsers = $derived(
    users.filter(user =>
        !trimmedQuery
            ? true
            : user.username.toLowerCase().includes(normalizedQuery) ||
              String(user.telegram_id).includes(trimmedQuery)
    )
)

function handleBotClick(item: Bot) {
    goto(resolve(`/app/bot/${item.uuid}`))
}

const handleUserClick: (item: Bot | User) => void = item => {
    if ('is_admin' in item) {
        goto(resolve(`/app/user/${item.telegram_id}`))
    }
}
</script>

<div class="mx-auto min-h-screen max-w-lg" aria-label="Bot management interface" role="application">
    <!-- Header Section -->
    <div class="mb-4 space-y-2 text-center text-2xl font-semibold">
        <!-- Logo and Main Title -->
        <div class="mb-2 flex flex-col items-center gap-4">
            <img
                class="h-20 w-20 transition-all duration-300 hover:scale-110 hover:rotate-3 sm:h-24 sm:w-24 md:h-28 md:w-28 lg:h-32 lg:w-32 xl:h-36 xl:w-36"
                alt="Bot Logo"
                src="/favicon.svg"
            />
            <h1 class="text-xl font-bold sm:text-2xl md:text-3xl lg:text-4xl xl:text-5xl">
                Feedback Bot Builder
            </h1>
        </div>
    </div>

    <!-- Search Bar -->
    <div class="relative my-4">
        <Search class="absolute end-4 top-1/2 h-5 w-5 -translate-y-1/2 transform text-gray-500" />
        <Input
            id="search-input"
            class="border border-primary ps-4"
            aria-label="Search bots or users"
            autocomplete="off"
            placeholder="Search bots or users..."
            type="text"
            bind:value={searchQuery}
        />
    </div>

    <!-- My Bots Section -->
    <ManagementCard
        emptyState={{
            message: searchQuery
                ? `No bots found matching "${searchQuery}"`
                : "You don't have any bots yet. Please add one.",
            subMessage: searchQuery ? '' : 'Click "Create a New Bot" to get started.'
        }}
        items={filteredBots}
        title="My bots"
    >
        <!-- Create New Bot Button -->
        {#snippet cta()}
            <AddButton icon="plus" label="Add new bot" route="/app/add_bot" variant="primary" />
        {/snippet}

        {#each filteredBots as bot (bot.telegram_id)}
            <ListItem item={bot} onClick={() => handleBotClick(bot)} type="bot" />
        {/each}
    </ManagementCard>

    {#if $session.isAdmin}
        <Separator class="my-8" />

        <!-- User Management Section -->
        <ManagementCard
            emptyState={{
                message: trimmedQuery
                    ? `No users found matching "${searchQuery}"`
                    : "You don't have any users yet.",
                subMessage: trimmedQuery ? '' : 'Click "Add new user" to get started.'
            }}
            items={filteredUsers}
            title="User Management"
        >
            <!-- Add New User Button -->
            {#snippet cta()}
                <AddButton
                    icon="user-plus"
                    label="Add new user"
                    route="/app/add_user"
                    variant="success"
                />
            {/snippet}

            {#each filteredUsers as user (user.telegram_id)}
                <ListItem item={user} onClick={() => handleUserClick(user)} type="user" />
            {/each}
        </ManagementCard>
    {/if}
</div>
