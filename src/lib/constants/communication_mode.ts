export type CommunicationMode = 'standard' | 'private' | 'anonymous'

export const communication_mode_options = (): {
    value: CommunicationMode
    title: string
    description: string
}[] => [
    {
        value: 'standard',
        title: 'Standard',
        description: 'Forward with usernames and profile links.'
    },
    {
        value: 'private',
        title: 'Private',
        description: 'Show only the public name; profile links removed.'
    },
    {
        value: 'anonymous',
        title: 'Anonymous',
        description: 'Replace identity with a request number.'
    }
]
