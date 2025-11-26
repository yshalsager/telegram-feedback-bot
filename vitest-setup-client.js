/// <reference types="@vitest/browser/matchers" />
/// <reference types="@vitest/browser/providers/playwright" />

import '@testing-library/jest-dom/vitest'
import {cleanup} from '@testing-library/svelte'
import {afterEach, beforeAll, vi} from 'vitest'
import {loadLocale} from 'wuchale/load-utils'
import '~/locales/main.loader.svelte.js'

// Ensure English catalog is available during component tests
beforeAll(async () => {
    await loadLocale('en')
})

// Ensure DOM is reset between component tests
afterEach(() => {
    cleanup()
    // Clear all mocks so Telegram SDK stubs don't leak across tests
    vi.clearAllMocks()
})
