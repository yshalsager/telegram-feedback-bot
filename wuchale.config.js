// @ts-check
import {adapter as svelte} from '@wuchale/svelte'
import {defineConfig} from 'wuchale'
import {adapter as js} from 'wuchale/adapter-vanilla'

export default defineConfig({
    sourceLocale: 'en',
    otherLocales: ['ar'],
    adapters: {
        main: svelte({
            files: ['./src/**/*.svelte', './src/**/*.svelte.{js,ts}'],
            catalog: './messages/{locale}/LC_MESSAGES/frontend',
            loaderPath: './src/lib/wuchale-loader.svelte.js'
        }),
        js: js({
            files: [
                // 'src/**/+{page,layout}.{js,ts}',
                'src/**/lib/i18n.{js,ts}',
                'src/lib/constants/**/*.ts'
            ],
            catalog: './messages/{locale}/LC_MESSAGES/frontend',
            loaderPath: './src/lib/wuchale-loader.js'
        })
    }
})
