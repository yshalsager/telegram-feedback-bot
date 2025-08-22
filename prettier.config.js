/** @type {import('prettier').Config} */
export default {
  plugins: ['prettier-plugin-svelte', 'prettier-plugin-tailwindcss'],
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
  tailwindStylesheet: './frontend/app.css'
};