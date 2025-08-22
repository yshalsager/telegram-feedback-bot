import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: adapter({
			fallback: 'index.html' // Enable SPA routing
		}),
		files: {
			src: 'frontend'
		},
	}
};

export default config;
