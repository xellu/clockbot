import { Account, type Profile } from "$lib/stores/Account";
import { temp } from "$lib/scripts/Temp";

export async function getProfile(): Promise<Profile | false> {
    const cached: Profile = temp.get("account")
    if (cached) { 
        Account.set(cached)
        return cached;
    }

    const r = await fetch('http://localhost:8100/auth/me')
    if (!r.ok) {
        Account.set(null)
        return false
    }

    const data: Profile = await r.json()

    temp.set("account", data)
    Account.set(data)
    return data
}