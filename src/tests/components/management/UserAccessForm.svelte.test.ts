import {readable} from 'svelte/store'
import {render, screen} from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import {describe, expect, it, vi} from 'vitest'
import UserAccessForm from '~/components/management/UserAccessForm.svelte'

vi.mock('$lib/i18n', () => ({
    availableLocales: readable([
        {locale: 'en', name: 'English'},
        {locale: 'ar', name: 'Arabic'}
    ])
}))

describe('UserAccessForm', () => {
    it('renders provided labels and locales', () => {
        render(UserAccessForm, {
            props: {
                usernameLabel: 'User handle',
                languageLabel: 'Preferred language',
                whitelistLabel: 'Allow list access',
                adminLabel: 'Super admin',
                submitLabel: 'Apply changes'
            }
        })

        expect(screen.getByLabelText('User handle')).toBeInTheDocument()
        expect(screen.getByLabelText('Preferred language')).toBeInTheDocument()
        expect(screen.getByRole('switch', {name: 'Allow list access'})).toBeInTheDocument()
        expect(screen.getByRole('switch', {name: 'Super admin'})).toBeInTheDocument()
        expect(screen.getByRole('option', {name: 'English'})).toBeInTheDocument()
        expect(screen.getByRole('option', {name: 'Arabic'})).toBeInTheDocument()
        expect(screen.getByRole('button', {name: 'Apply changes'})).toBeInTheDocument()
    })

    it('submits when enabled and values are changed', async () => {
        const submit_handler = vi.fn()
        const user = userEvent.setup()

        render(UserAccessForm, {
            props: {
                username: 'existing',
                languageCode: 'en',
                isWhitelisted: true,
                isAdmin: false,
                onsubmit: submit_handler
            }
        })

        const username_input = screen.getByLabelText('Username') as HTMLInputElement
        const language_select = screen.getByLabelText('Language') as HTMLSelectElement
        const admin_switch = screen.getByRole('switch', {name: 'Admin access'})
        const submit_button = screen.getByRole('button', {name: 'Save'})

        await user.clear(username_input)
        await user.type(username_input, 'newname')
        await user.selectOptions(language_select, 'ar')
        await user.click(admin_switch)

        expect(admin_switch).toHaveAttribute('aria-checked', 'true')

        await user.click(submit_button)

        expect(submit_handler).toHaveBeenCalledTimes(1)
    })

    it('does not submit when disabled', async () => {
        const submit_handler = vi.fn()
        const user = userEvent.setup()

        render(UserAccessForm, {
            props: {
                submitDisabled: true,
                onsubmit: submit_handler
            }
        })

        const submit_button = screen.getByRole('button', {name: 'Save'})
        expect(submit_button).toBeDisabled()

        await user.click(submit_button)

        expect(submit_handler).not.toHaveBeenCalled()
    })
})
