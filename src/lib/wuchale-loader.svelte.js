// This is just the default loader.
// You can customize it however you want, it will not be overwritten once it exists and is not empty.

/// <reference types="wuchale/virtual" />

import {key, loadCatalog, loadIDs} from 'virtual:wuchale/proxy' // or proxy/sync
import {defaultCollection, registerLoaders} from 'wuchale/load-utils'

const catalogs = $state({})

// for non-reactive
export const get = registerLoaders(key, loadCatalog, loadIDs, defaultCollection(catalogs))

// same function, only will be inside $derived when used
export default get
