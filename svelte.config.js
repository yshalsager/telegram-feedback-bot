import adapter from '@sveltejs/adapter-static'
import {vitePreprocess} from '@sveltejs/vite-plugin-svelte'

/** @type {import('@sveltejs/kit').Config} */
const config = {
    preprocess: [vitePreprocess()],
    kit: {
        adapter: adapter({
            fallback: 'index.html' // Enable SPA routing
        }),
        alias: {
            '~': './frontend',
            $lib: './frontend/lib'
        },
        files: {
            src: 'frontend' // TODO: remove this after removing old src
        },
        output: {
            bundleStrategy: 'inline'
        },
        paths: {
            base: '/app'
        }
    }
}

export default config
