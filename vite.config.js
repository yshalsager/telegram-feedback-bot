import { paraglideVitePlugin } from '@inlang/paraglide-js';
import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [
		tailwindcss(),
		sveltekit(),
		paraglideVitePlugin({
			project: './project.inlang',
			outdir: './frontend/lib/paraglide'
		})
	],
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
				secure: true,
			},
			'/webhook': {
				target: `http://localhost:${process.env.GRANIAN_PORT}`,
				changeOrigin: true,
				secure: true,
			}
		}
	},
	test: {
		expect: { requireAssertions: true },
		projects: [
			{
				extends: './vite.config.js',
				test: {
					name: 'client',
					environment: 'browser',
					browser: {
						enabled: true,
						provider: 'playwright',
						instances: [{ browser: 'chromium' }]
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
});
