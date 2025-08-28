import {paraglideVitePlugin} from '@inlang/paraglide-js'
import tailwindcss from '@tailwindcss/vite'
import {sveltekit} from '@sveltejs/kit/vite'
import {defineConfig} from 'vite'
import path from 'path'
import {compression, defineAlgorithm} from 'vite-plugin-compression2'

export default defineConfig({
    plugins: [
        tailwindcss(),
        sveltekit(),
        paraglideVitePlugin({
            project: './project.inlang',
            outdir: './frontend/lib/paraglide'
        }),
        compression({
            algorithms: ['gzip', 'brotliCompress', defineAlgorithm('deflate', {level: 9})],
            threshold: 1000 // Only compress files larger than 1KB
        })
    ],
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
