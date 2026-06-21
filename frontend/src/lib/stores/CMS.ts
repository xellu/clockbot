import { writable, type Writable } from "svelte/store";

export type ContentType = {
    name: string,
    color: string,
    
    mcIp: string,
    discordInvite: string,
    
    discordClientId: number,
    domain: string,
}

export let CMS: Writable<ContentType | null> = writable(null)
