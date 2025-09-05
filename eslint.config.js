import prettier from 'eslint-config-prettier'
import {includeIgnoreFile} from '@eslint/compat'
import js from '@eslint/js'
import svelte from 'eslint-plugin-svelte'
import globals from 'globals'
import {fileURLToPath} from 'node:url'
import svelteConfig from './svelte.config.js'
import tseslint from 'typescript-eslint'

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
            'svelte/no-navigation-without-resolve': ['error', {ignoreLinks: true}]
        }
    }
]
