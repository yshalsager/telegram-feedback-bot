import {render, screen} from '@testing-library/svelte'
import {beforeEach, describe, expect, it, vi} from 'vitest'
import Page from '~/routes/+page.svelte'

const listBotsMock = vi.fn()
const listUsersMock = vi.fn()

vi.mock('$lib/api.js', () => ({
    list_bots: (...args) => listBotsMock(...args),
    list_users: (...args) => listUsersMock(...args)
}))

vi.mock('$app/navigation', () => ({
    goto: vi.fn()
}))

vi.mock('$app/paths', () => ({
    resolve: (path: string) => path
}))

describe('root +page.svelte', () => {
    beforeEach(() => {
        listBotsMock.mockResolvedValue([])
        listUsersMock.mockResolvedValue([])
    })

    it('renders the primary heading', () => {
        render(Page)

        expect(screen.getByRole('heading', {level: 1})).toBeInTheDocument()
    })
})
