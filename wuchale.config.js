// @ts-check
import {defineConfig} from 'wuchale'
import {adapter as svelte} from '@wuchale/svelte'

export default defineConfig({
    sourceLocale: 'en',
    otherLocales: ['ar'],
    adapters: {
        main: svelte({
            files: ['./frontend/**/*.svelte', './frontend/**/*.svelte.{js,ts}'],
            catalog: './messages/{locale}/LC_MESSAGES/frontend',
            loaderPath: './frontend/lib/wuchale-loader.svelte.js'
        })
    }
})
