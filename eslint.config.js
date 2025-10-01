import {fileURLToPath} from 'node:url'
import {includeIgnoreFile} from '@eslint/compat'
import js from '@eslint/js'
import prettier from 'eslint-config-prettier'
import svelte from 'eslint-plugin-svelte'
import globals from 'globals'
import tseslint from 'typescript-eslint'
import svelteConfig from './svelte.config.js'

const gitignorePath = fileURLToPath(new URL('./.gitignore', import.meta.url))

/** @type {import('eslint').Linter.Config[]} */
export default [
    includeIgnoreFile(gitignorePath),
    js.configs.recommended,
    ...tseslint.configs.recommended,
    ...svelte.configs.recommended,
    prettier,
    ...svelte.configs.prettier,
    {
        languageOptions: {
            globals: {...globals.browser, ...globals.node}
        }
    },
    {
        files: ['**/*.svelte', '**/*.svelte.ts', '**/*.svelte.js'],
        languageOptions: {
            parserOptions: {
                projectService: true,
                extraFileExtensions: ['.svelte'],
                parser: tseslint.parser,
                svelteConfig
            }
        }
    },
    {
        files: ['**/*.js'],
        rules: {
            'no-explicit-any': 'off'
        }
    },
    {
        files: ['**/*.svelte'],
        rules: {
            // Enable TypeScript import type rules for Svelte files
            '@typescript-eslint/consistent-type-imports': 'error',
            '@typescript-eslint/no-import-type-side-effects': 'error',
            // Allow href attributes in button components that handle resolution internally
            'svelte/no-navigation-without-resolve': ['error', {ignoreLinks: true}],
            'svelte/sort-attributes': [
                'error',
                {
                    order: [
                        'this',
                        'bind:this',
                        'id',
                        'name',
                        'slot',
                        {match: '/^--/u', sort: 'alphabetical'},
                        ['style', '/^style:/u'],
                        'class',
                        {match: '/^class:/u', sort: 'alphabetical'},
                        {
                            match: ['!/:/u', '!/^(?:this|id|name|style|class)$/u', '!/^--/u'],
                            sort: 'alphabetical'
                        },
                        ['/^bind:/u', '!bind:this', '/^on:/u'],
                        {match: '/^use:/u', sort: 'alphabetical'},
                        {match: '/^transition:/u', sort: 'alphabetical'},
                        {match: '/^in:/u', sort: 'alphabetical'},
                        {match: '/^out:/u', sort: 'alphabetical'},
                        {match: '/^animate:/u', sort: 'alphabetical'},
                        {match: '/^let:/u', sort: 'alphabetical'}
                    ]
                }
            ]
        }
    }
]
