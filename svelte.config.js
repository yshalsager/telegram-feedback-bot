import adapter from '@sveltejs/adapter-static'

/** @type {import('@sveltejs/kit').Config} */
const config = {
    kit: {
        adapter: adapter({
            fallback: 'index.html' // Enable SPA routing
        }),
        files: {
            src: 'frontend' // TODO: remove this after removing old src
        },
        output: {
            bundleStrategy: 'single'
        }
    }
}

export default config
