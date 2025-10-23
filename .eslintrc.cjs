module.exports = {
    root: true,
    extends: ['@sveltejs/eslint-config', '@sveltejs/eslint-config/kit', 'prettier'],
    parserOptions: {
        project: './tsconfig.eslint.json'
    },
    ignorePatterns: ['src/.svelte-kit/**', '.svelte-kit/**'],
    overrides: [
        {
            files: ['src/routes/**', 'src/lib/**', 'src/components/**'],
            parserOptions: {
                project: './tsconfig.eslint.json'
            }
        }
    ]
}
