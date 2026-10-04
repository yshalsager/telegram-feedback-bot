import {defineEnvVars} from '@sveltejs/kit/env'

export const variables = defineEnvVars({
    PUBLIC_DEBUG: {public: true, schema: input => input ?? ''}
})
