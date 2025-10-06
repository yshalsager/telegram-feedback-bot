import path from 'path'
import {sveltekit} from '@sveltejs/kit/vite'
import tailwindcss from '@tailwindcss/vite'
import {wuchale} from '@wuchale/vite-plugin'
import {defineConfig} from 'vite'
import domain from 'vite-plugin-domain'

const wuchalePlugin = wuchale()

if (process.env.VITEST) {
    const originalLoad = wuchalePlugin.load?.bind(wuchalePlugin)
    if (originalLoad) {
        wuchalePlugin.load = id => {
            const normalized =
                typeof id === 'string'
                    ? id.replace('?er=', '?importer=').replace('?origin=', '?importer=')
                    : id
            return originalLoad(normalized)
        }
    }
}

export default defineConfig({
    plugins: [
        tailwindcss(),
        wuchalePlugin,
        sveltekit(),
        domain({nameSource: 'pkg', tld: 'localhost'})
    ],
    resolve: {
        alias: [{find: '~', replacement: path.resolve('frontend')}],
        conditions: process.env.VITEST ? ['browser'] : undefined
    },
    server: {
        allowedHosts: [
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            ...(process.env.TELEGRAM_BUILDER_BOT_WEBHOOK_URL
                ? [process.env.TELEGRAM_BUILDER_BOT_WEBHOOK_URL.replace(/^https?:\/\//, '')]
                : [])
        ],
        fs: {
            allow: ['./frontend']
        },
        port: process.env.VITE_PORT ? parseInt(process.env.VITE_PORT) : 5173,
        host: true,
        proxy: {
            '/api': {
                target: `http://localhost:${process.env.GRANIAN_PORT}`,
                changeOrigin: true,
                secure: true
            }
        }
    },
    test: {
        expect: {requireAssertions: true},
        projects: [
            {
                extends: './vite.config.js',
                test: {
                    name: 'components',
                    environment: 'jsdom',
                    include: ['frontend/**/*.svelte.{test,spec}.{js,ts}'],
                    exclude: ['frontend/lib/server/**'],
                    setupFiles: ['./vitest-setup-client.js']
                }
            },
            {
                extends: './vite.config.js',
                test: {
                    name: 'server',
                    environment: 'node',
                    include: ['frontend/**/*.{test,spec}.{js,ts}'],
                    exclude: ['frontend/**/*.svelte.{test,spec}.{js,ts}']
                }
            }
        ]
    }
})
