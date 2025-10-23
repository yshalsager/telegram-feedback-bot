import {render, screen} from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import {describe, expect, it} from 'vitest'
import SwitchRow from '~/components/management/SwitchRow.svelte'

describe('SwitchRow', () => {
    it('renders label and description', () => {
        render(SwitchRow, {
            props: {
                id: 'confirmations-toggle',
                label: 'Message received confirmations',
                description: 'Send a notification when feedback arrives',
                checked: false
            }
        })

        expect(screen.getByText('Send a notification when feedback arrives')).toBeInTheDocument()
        expect(
            screen.getByRole('switch', {name: /message received confirmations/i})
        ).toBeInTheDocument()
    })

    it('toggles the switch when clicked', async () => {
        const user = userEvent.setup()
        render(SwitchRow, {
            props: {
                id: 'confirmations-toggle',
                label: 'Message received confirmations',
                checked: false
            }
        })

        const toggle = screen.getByRole('switch', {
            name: /message received confirmations/i
        })

        expect(toggle).toHaveAttribute('aria-checked', 'false')

        await user.click(toggle)

        expect(toggle).toHaveAttribute('aria-checked', 'true')
    })
})
