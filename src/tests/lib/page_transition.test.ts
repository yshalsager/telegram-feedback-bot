import {onNavigate} from '$app/navigation'
import {afterEach, expect, it, vi} from 'vitest'
import {setPageTransition} from '#lib/page_transition.js'

vi.mock('$app/navigation', () => ({onNavigate: vi.fn()}))

afterEach(() => vi.unstubAllGlobals())

it('skips shallow navigations and waits for full navigation transitions', async () => {
    let completed = false
    const startViewTransition = vi.fn(callback => callback().then(() => (completed = true)))
    vi.stubGlobal('document', {startViewTransition})
    setPageTransition()
    const navigate = vi.mocked(onNavigate).mock.calls[0][0]

    await navigate({shallow: true} as Parameters<typeof navigate>[0])
    expect(startViewTransition).not.toHaveBeenCalled()

    const {promise, resolve} = Promise.withResolvers<void>()
    await navigate({shallow: false, complete: promise} as Parameters<typeof navigate>[0])
    expect(startViewTransition).toHaveBeenCalledOnce()
    expect(completed).toBe(false)

    resolve()
    await startViewTransition.mock.results[0].value
    expect(completed).toBe(true)
})
