export type CommunicationMode = 'standard' | 'private' | 'anonymous'

// @wc-include
export const communication_mode_options: {
    value: CommunicationMode
    title: string
    description: string
}[] = [
    {
        value: 'standard', // @wc-ignore
        title: 'Standard',
        description: 'Forward with usernames and profile links.'
    },
    {
        value: 'private', // @wc-ignore
        title: 'Private',
        description: 'Show only the public name; profile links removed.'
    },
    {
        value: 'anonymous', // @wc-ignore
        title: 'Anonymous',
        description: 'Replace identity with a request number.'
    }
]
