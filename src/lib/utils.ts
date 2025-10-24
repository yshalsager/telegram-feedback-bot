import {clsx} from 'clsx'
import type {ClassValue} from 'clsx'
import {twMerge} from 'tailwind-merge'

type ElementLike = Element | HTMLElement | SVGElement

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

export type WithElementRef<T, ElementType extends ElementLike = ElementLike> = T & {
    ref?: ElementType | null
}

export type WithoutChildren<T> = Omit<T, 'children'>

export type WithoutChildrenOrChild<T> = Omit<T, 'child' | 'children'>
