<script lang="ts">
// @wc-ignore-file
import {
    ArrowUpRight,
    Bot,
    GitBranch,
    MessageSquare,
    Send,
    ShieldCheck,
    Sparkles,
    Users
} from '@lucide/svelte'
import {Button} from '~/lib/components/ui/button'
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle
} from '~/lib/components/ui/card'
import {Separator} from '~/lib/components/ui/separator'

const github_url = 'https://github.com/yshalsager/telegram-feedback-bot'
const project_logo = '/favicon.svg'

type Icon = typeof Bot

type NavLink = {
    href: string
    label: string
}

type FeatureCard = {
    icon: Icon
    title: string
    description: string
}

type ToolkitItem = {
    title: string
    summary: string
    points: string[]
}

type Step = {
    icon: Icon
    title: string
    description: string
}

type Screenshot = {
    src: string
    alt: string
    caption: string
    mobile?: boolean
}

const nav_links: NavLink[] = [
    {href: '#features', label: 'Features'},
    {href: '#toolkit', label: 'What’s inside'},
    {href: '#gallery', label: 'Screenshots'},
    {href: '#privacy', label: 'Privacy'}
]

const features: FeatureCard[] = [
    {
        icon: MessageSquare,
        title: 'Handle feedback where it arrives',
        description:
            'Conversations stay in Telegram with polite confirmations and mirrored replies, so chats feel natural for everyone.'
    },
    {
        icon: Users,
        title: 'Share the dashboard safely',
        description:
            'Owners whitelist trusted users, who can add bots, tweak messages, and help moderate while you supervise.'
    },
    {
        icon: ShieldCheck,
        title: 'Keep oversight simple',
        description:
            'Pause tokens, choose allowed media, and keep an eye on stats and ban lists from a calm workspace.'
    }
]

const toolkit: ToolkitItem[] = [
    {
        title: 'Builder bot',
        summary: 'Lives in chats you already use and gives owners quick commands.',
        points: [
            'Share the mini app link with /start',
            'Broadcast updates to whitelisted users',
            'Pause or restart bots when something feels off'
        ]
    },
    {
        title: 'Mini app dashboard',
        summary: 'Opens inside Telegram for owners and whitelisted users.',
        points: [
            'Add bots, rotate tokens, and update messages',
            'Choose allowed media types and set cooldowns',
            'Link groups or chats for tidy threading'
        ]
    },
    {
        title: 'Feedback bots',
        summary: 'Forward messages, mirror replies, and keep users in the loop automatically.',
        points: [
            'Use topics or direct chats to keep conversations tidy',
            'Send polite auto-replies and reflect edits both ways',
            'Handle loads efficiently using Telegram webhooks instead of polling',
            'Ban or unblock users when moderation is needed'
        ]
    }
]

const workflow_steps: Step[] = [
    {
        icon: Sparkles,
        title: 'Connect the builder bot',
        description:
            'Self-host the Django + python-telegram-bot stack, point BotFather to the webhook, and unlock the inline menu.'
    },
    {
        icon: Users,
        title: 'Shape the moderator experience',
        description:
            'Configure languages, message presets, media policies, and anonymous or private forwarding modes that fit your community.'
    },
    {
        icon: Send,
        title: 'Moderate and broadcast confidently',
        description:
            'Handle incoming threads, rotate tokens with approval, and broadcast announcements using filters like joined dates or activity.'
    }
]

const screenshots: Screenshot[] = [
    {
        src: '/screenshots/app-dashboard-mobile.png',
        alt: 'Mobile dashboard listing managed bots and whitelisted users',
        caption:
            'Home view shows moderated bots and whitelisted users with quick actions, optimized for Telegram in-app use.',
        mobile: true
    },
    {
        src: '/screenshots/app-bot-detail-mobile.png',
        alt: 'Bot detail screen with media controls, token rotation, and stats cards',
        caption:
            'Per-bot management centralizes status controls, message presets, media policy, and throughput counters.',
        mobile: true
    },
    {
        src: '/screenshots/app-add-bot-mobile.png',
        alt: 'Add bot workflow capturing token, receipt text, and communication mode',
        caption:
            'Adding a new feedback bot guides owners through token validation, messaging, and communication rules.',
        mobile: true
    },
    {
        src: '/screenshots/app-add-user-mobile.png',
        alt: 'User provisioning form with whitelist and admin toggles',
        caption:
            'User management handles whitelist, language, and admin roles without leaving the Telegram shell.',
        mobile: true
    }
]

const current_year = new Date().getFullYear()

const screenshot_wrapper_base =
    'flex justify-center overflow-hidden rounded-2xl border border-border/60 bg-muted/30 shadow-inner'
const screenshot_wrapper_mobile = `${screenshot_wrapper_base} p-4 sm:p-6`

const screenshot_image_mobile =
    'transition mx-auto h-auto max-h-[680px] w-auto max-w-full rounded-[1.5rem] border border-border/50 bg-background object-contain shadow-md'
const screenshot_image_default = 'transition w-full rounded-xl object-cover'

function screenshot_wrapper_class(shot: Screenshot): string {
    return shot.mobile ? screenshot_wrapper_mobile : screenshot_wrapper_base
}

function screenshot_image_class(shot: Screenshot): string {
    return shot.mobile ? screenshot_image_mobile : screenshot_image_default
}
</script>

<svelte:head>
    <title>Telegram Feedback Bots Builder</title>
    <meta
        name="description"
        content="Self-hosted toolkit for provisioning and operating Telegram feedback bots with a builder bot, mini app dashboard, and moderation tools."
    />
</svelte:head>

<header class="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur">
    <div class="mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-4">
        <a class="flex items-center gap-3 font-semibold tracking-tight" href="#top">
            <img
                class="h-10 w-10 rounded-lg border border-border/60 p-1.5"
                alt="Telegram Feedback Bots Builder logo"
                src={project_logo}
            />
            <span class="text-lg">Telegram Feedback Bots Builder</span>
        </a>
        <nav class="hidden items-center gap-6 text-sm font-medium lg:flex">
            {#each nav_links as link (link.href)}
                <a
                    class="text-muted-foreground transition hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:ring-offset-2 focus-visible:ring-offset-background focus-visible:outline-none"
                    href={link.href}
                >
                    {link.label}
                </a>
            {/each}
        </nav>
        <div class="hidden items-center gap-3 lg:flex">
            <Button href={github_url} size="sm">
                GitHub
                <ArrowUpRight class="size-4" aria-hidden="true" />
            </Button>
        </div>
        <div class="flex items-center gap-3 lg:hidden">
            <Button aria-label="Open GitHub repository" href={github_url} size="icon-sm">
                <GitBranch class="size-5" aria-hidden="true" />
            </Button>
        </div>
    </div>
</header>

<main id="top" class="mx-auto flex max-w-6xl flex-col gap-24 px-6 py-16 lg:py-24">
    <section class="space-y-10">
        <div class="space-y-6">
            <div class="flex items-center gap-2 text-sm font-medium text-primary">
                <Sparkles class="size-4" aria-hidden="true" />
                <span>Free & open source · Telegram native</span>
            </div>
            <h1 class="text-4xl font-bold tracking-tight text-balance sm:text-5xl lg:text-6xl">
                Operate feedback bots without leaving Telegram.
            </h1>
            <p class="max-w-2xl text-lg text-muted-foreground">
                Add your own feedback bots, whitelist the operators you trust, and keep every reply
                inside Telegram. The builder bot, mini app, and worker bots are all bundled for you.
            </p>
            <div class="flex flex-wrap items-center gap-4">
                <Button href={github_url} size="lg">
                    View on GitHub
                    <ArrowUpRight class="size-5" aria-hidden="true" />
                </Button>
                <Button href={`${github_url}#setup`} size="lg" variant="outline">
                    Read setup guide
                    <GitBranch class="size-5" aria-hidden="true" />
                </Button>
            </div>
        </div>
    </section>

    <section id="features" class="space-y-8">
        <div class="flex flex-col gap-4 text-center">
            <span
                class="mx-auto inline-flex items-center gap-2 rounded-full bg-secondary px-4 py-1 text-xs font-semibold tracking-wide text-secondary-foreground uppercase"
            >
                Toolkit features
            </span>
            <h2 class="text-3xl font-semibold tracking-tight sm:text-4xl">
                Feel at home inside Telegram
            </h2>
            <p class="mx-auto max-w-2xl text-base text-muted-foreground">
                Telegram Feedback Bots Builder gives support, product, and community teams a
                dependable place to collect and answer feedback without juggling extra tools.
            </p>
        </div>
        <div class="grid gap-6 md:grid-cols-3">
            {#each features as feature (feature.title)}
                <Card class="h-full border-border/70 bg-card/80">
                    <CardHeader class="space-y-4 text-center">
                        {@const Icon = feature.icon}
                        <div
                            class="mx-auto flex size-12 items-center justify-center rounded-full bg-primary/10 text-primary"
                        >
                            <Icon class="size-6" aria-hidden="true" />
                        </div>
                        <CardTitle class="text-lg font-semibold">{feature.title}</CardTitle>
                        <CardDescription class="text-sm leading-relaxed text-muted-foreground">
                            {feature.description}
                        </CardDescription>
                    </CardHeader>
                </Card>
            {/each}
        </div>
    </section>

    <section id="toolkit" class="space-y-10">
        <div class="flex flex-col gap-3 text-center">
            <h2 class="text-3xl font-semibold tracking-tight sm:text-4xl">
                Everything you need in one toolkit
            </h2>
            <p class="mx-auto max-w-2xl text-base text-muted-foreground">
                Three pieces work together out of the box: a builder bot to run commands, a
                dashboard you can open inside Telegram, and feedback bots that do the heavy lifting
                for every conversation.
            </p>
        </div>
        <div class="grid gap-6 md:grid-cols-3">
            {#each toolkit as item (item.title)}
                <Card class="h-full border-border/70 bg-card/80">
                    <CardHeader class="space-y-2">
                        <CardTitle class="text-lg font-semibold">{item.title}</CardTitle>
                        <CardDescription class="text-sm text-muted-foreground"
                            >{item.summary}</CardDescription
                        >
                    </CardHeader>
                    <CardContent class="space-y-2">
                        <ul class="space-y-2 text-sm text-muted-foreground">
                            {#each item.points as point (point)}
                                <li class="flex items-start gap-2">
                                    <span
                                        class="mt-1 size-1.5 rounded-full bg-primary/70"
                                        aria-hidden="true"
                                    ></span>
                                    <span>{point}</span>
                                </li>
                            {/each}
                        </ul>
                    </CardContent>
                </Card>
            {/each}
        </div>
    </section>

    <section id="gallery" class="space-y-8">
        <div class="flex flex-col gap-3 text-center">
            <h2 class="text-3xl font-semibold tracking-tight sm:text-4xl">Screenshots</h2>
            <p class="mx-auto max-w-2xl text-base text-muted-foreground">
                Take a peek at the mini app whitelisted users see when they use the dashboard.
            </p>
        </div>
        <div class="grid gap-6 lg:grid-cols-2">
            {#each screenshots as shot (shot.src)}
                <Card class="overflow-hidden border-border/70 bg-card/80">
                    <CardContent class="space-y-4 p-6">
                        <figure class="space-y-4">
                            <a
                                class={screenshot_wrapper_class(shot)}
                                href={shot.src}
                                rel="noopener noreferrer"
                                target="_blank"
                            >
                                <img
                                    class={screenshot_image_class(shot)}
                                    alt={shot.alt}
                                    loading="lazy"
                                    src={shot.src}
                                />
                            </a>
                            <figcaption class="text-sm text-muted-foreground">
                                {shot.caption}
                            </figcaption>
                        </figure>
                    </CardContent>
                </Card>
            {/each}
        </div>
    </section>

    <section
        id="open-source"
        class="grid gap-8 lg:grid-cols-[0.9fr_minmax(0,1.1fr)] lg:items-center"
    >
        <Card class="border-border/70 bg-card/80">
            <CardHeader>
                <div class="flex items-center gap-2 text-sm font-medium text-primary">
                    <GitBranch class="size-4" aria-hidden="true" />
                    <span>Open source</span>
                </div>
                <CardTitle class="text-3xl font-semibold">Licensed under GPLv3</CardTitle>
                <CardDescription class="text-base leading-relaxed text-muted-foreground">
                    The entire project lives on GitHub, free and open source. Built with
                    battle-tested Django, python-telegram-bot, and SvelteKit, it is ready for teams
                    that prefer to run and extend it themselves.
                </CardDescription>
            </CardHeader>
            <CardFooter class="flex flex-wrap items-center gap-3">
                <Button href={github_url}>
                    Star on GitHub
                    <ArrowUpRight class="size-4" aria-hidden="true" />
                </Button>
                <Button href={`${github_url}/blob/master/LICENSE`} variant="outline">
                    Read the GPLv3 license
                </Button>
            </CardFooter>
        </Card>
        <Card class="border-dashed border-border/70 bg-card/60">
            <CardContent class="space-y-4 p-6">
                <p class="text-sm text-muted-foreground">
                    Developed with a stack that favors openness over lock-in. Issues and pull
                    requests are welcome—start with the README for setup and contribution
                    guidelines.
                </p>
                <Separator />
                <ul class="space-y-3 text-sm text-muted-foreground">
                    <li class="flex items-start gap-3">
                        <Bot class="mt-0.5 size-5 text-primary" aria-hidden="true" />
                        <span
                            >Builder bot, dashboard, and worker processes run together via Docker or
                            mise + uv + pnpm.</span
                        >
                    </li>
                    <li class="flex items-start gap-3">
                        <GitBranch class="mt-0.5 size-5 text-primary" aria-hidden="true" />
                        <span
                            >Granian and Django serve the built mini app directly—no reverse proxy
                            or SSR juggling required.</span
                        >
                    </li>
                    <li class="flex items-start gap-3">
                        <ShieldCheck class="mt-0.5 size-5 text-primary" aria-hidden="true" />
                        <span
                            >Encrypted token storage and admin review keep credentials safe even
                            when rotating frequently.</span
                        >
                    </li>
                </ul>
            </CardContent>
        </Card>
    </section>

    <section id="privacy" class="space-y-8">
        <div class="flex flex-col gap-3 text-center">
            <h2 class="text-3xl font-semibold tracking-tight sm:text-4xl">
                Your data stays with you
            </h2>
            <p class="mx-auto max-w-2xl text-base text-muted-foreground">
                We publish the code and you decide where to run it. Everything stored is there only
                to route chats and help moderators stay in sync.
            </p>
        </div>
        <Card class="border-border/70 bg-card/80">
            <CardContent class="space-y-4 p-6">
                <ul class="space-y-3 text-sm text-muted-foreground">
                    <li>
                        <strong class="text-foreground">Only essentials:</strong> bot tokens stay encrypted,
                        and we keep IDs—not message contents—to map conversations.
                    </li>
                    <li>
                        <strong class="text-foreground">You hold the keys:</strong> delete chats, rotate
                        tokens, or wipe the database whenever you choose.
                    </li>
                    <li>
                        <strong class="text-foreground">No hidden services:</strong> there are no bundled
                        analytics or telemetry—deploy it where you are comfortable.
                    </li>
                </ul>
                <p class="text-sm text-muted-foreground">
                    Want the full breakdown? Read the
                    <a
                        class="underline"
                        href={`${github_url}/blob/master/PRIVACY_POLICY.md`}
                        rel="noopener noreferrer"
                        target="_blank"
                    >
                        Privacy Policy
                    </a>
                    that ships with the project.
                </p>
            </CardContent>
        </Card>
    </section>

    <section id="workflow" class="space-y-8">
        <div class="flex flex-col gap-3 text-center">
            <h2 class="text-3xl font-semibold tracking-tight sm:text-4xl">How it works</h2>
            <p class="mx-auto max-w-2xl text-base text-muted-foreground">
                Bring the bots online in three focused steps.
            </p>
        </div>
        <div class="grid gap-6 md:grid-cols-3">
            {#each workflow_steps as step, index (step.title)}
                <Card class="h-full border-border/70 bg-card/80">
                    <CardHeader class="space-y-4">
                        {@const Icon = step.icon}
                        <div class="flex items-center gap-3 text-sm font-semibold">
                            <span
                                class="flex size-9 items-center justify-center rounded-full bg-primary/10 text-primary"
                                >{index + 1}</span
                            >
                            <Icon class="size-5 text-primary" aria-hidden="true" />
                            <span class="text-base">{step.title}</span>
                        </div>
                        <CardDescription class="text-sm leading-relaxed text-muted-foreground"
                            >{step.description}</CardDescription
                        >
                    </CardHeader>
                </Card>
            {/each}
        </div>
    </section>

    <section class="rounded-3xl border border-border/80 bg-card/80 p-10 text-center shadow-xl">
        <h2 class="text-3xl font-semibold tracking-tight sm:text-4xl">
            Bring your Telegram feedback loop online
        </h2>
        <p class="mt-4 text-base text-muted-foreground">
            Deploy Telegram Feedback Bots Builder, invite your moderators, and keep conversations
            flowing in real time.
        </p>
        <div class="mt-8 flex flex-wrap justify-center gap-4">
            <Button href={github_url} size="lg">
                Explore the code
                <GitBranch class="size-5" aria-hidden="true" />
            </Button>
        </div>
    </section>
</main>

<footer class="mx-auto w-full max-w-6xl px-6 pb-12 text-sm text-muted-foreground">
    <Separator class="mb-6" />
    <div class="flex flex-col gap-3 text-center sm:flex-row sm:items-center sm:justify-between">
        <p>
            © {current_year} Telegram Feedback Bots Builder. Developed by
            <a
                class="transition hover:text-foreground"
                href="https://github.com/yshalsager"
                target="_blank">yshalsager</a
            >.
        </p>
        <div class="flex items-center justify-center gap-4">
            <a class="transition hover:text-foreground" href={github_url} target="_blank">GitHub</a>
        </div>
    </div>
</footer>
