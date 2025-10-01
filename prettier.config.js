/** @type {import('prettier').Config} */
export default {
    plugins: [
        '@ianvs/prettier-plugin-sort-imports',
        'prettier-plugin-svelte',
        'prettier-plugin-tailwindcss'
    ],
    semi: false,
    singleQuote: true,
    tabWidth: 4,
    trailingComma: 'none',
    printWidth: 100,
    quoteProps: 'as-needed',
    bracketSpacing: false,
    arrowParens: 'avoid',
    overrides: [
        {
            files: '*.js',
            options: {
                tabWidth: 4
            }
        },
        {
            files: ['*.html', '*.css'],
            options: {
                tabWidth: 2
            }
        },
        {
            files: '*.svelte',
            options: {
                tabWidth: 4,
                parser: 'svelte',
                svelteStrictMode: false,
                svelteSortOrder: 'scripts-options-markup-styles',
                svelteIndentScriptAndStyle: false
            }
        }
    ],
    importOrder: [
        '^(svelte|@sveltejs/kit|\\$app)',
        '<THIRD_PARTY_MODULES>',
        '^(\\$lib|~)(/.*)?$',
        '^[./]'
    ],
    importOrderParserPlugins: ['svelte', 'typescript', 'decorators-legacy'],
    tailwindStylesheet: './frontend/app.css'
}
