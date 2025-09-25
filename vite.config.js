import {sveltekit} from '@sveltejs/kit/vite'
import tailwindcss from '@tailwindcss/vite'
import {wuchale} from '@wuchale/vite-plugin'
import path from 'path'
import {defineConfig} from 'vite'

export default defineConfig({
    plugins: [tailwindcss(), wuchale(), sveltekit()],
    resolve: {
        alias: [{find: '~', replacement: path.resolve('frontend')}]
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
                    name: 'client',
                    environment: 'browser',
                    browser: {
                        enabled: true,
                        provider: 'playwright',
                        instances: [{browser: 'chromium'}]
                    },
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
