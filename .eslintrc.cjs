module.exports = {
    root: true,
    extends: ['@sveltejs/eslint-config', '@sveltejs/eslint-config/kit', 'prettier'],
    parserOptions: {
        project: './tsconfig.eslint.json'
    },
    ignorePatterns: ['frontend/.svelte-kit/**', '.svelte-kit/**'],
    overrides: [
        {
            files: ['frontend/routes/**', 'frontend/lib/**', 'frontend/components/**'],
            parserOptions: {
                project: './tsconfig.eslint.json'
            }
        }
    ]
}
