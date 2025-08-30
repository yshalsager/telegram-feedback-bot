import {onNavigate} from '$app/navigation'

export const setPageTransition = () => {
    onNavigate(async navigation => {
        if (!document.startViewTransition) {
            return
        }

        return new Promise(oldStateCaptureResolve => {
            document.startViewTransition(async () => {
                oldStateCaptureResolve()
                await navigation.complete
            })
        })
    })
}
