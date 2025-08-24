import adapter from '@sveltejs/adapter-static'

/** @type {import('@sveltejs/kit').Config} */
const config = {
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
        }
    }
}

export default config
