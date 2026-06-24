import { temp } from "$lib/scripts/Temp"
import { writable, type Writable } from "svelte/store"

export type Profile = {
    discord: number,
    minecraft: string,

    last_seen: null | number,
    isAdmin: boolean,

    whitelist: {
        status: "Inactive" | "Pending" | "Rejected" | "Approved",
        moderator: number | null,
        reapply_in: number | null,
        reason: string | null,
        answers: {question: string, answer: string}[],

        created_at: number
    }
} | null

export const Account: Writable<Profile> = writable(null)