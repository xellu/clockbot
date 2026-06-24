<script lang="ts">
    import Loader from "$lib/components/Loader.svelte";
  import { getProfile } from "$lib/scripts/Auth";
    
    import { temp } from "$lib/scripts/Temp";
    import { onMount } from "svelte";
    
    let error: null | string = $state(null)
    onMount(async () => {
        const search = new URLSearchParams(window.location.search)
        if (!search.has("code")) {
            error = "No code provided"
            return;
        }

        //TODO: replace with just /
        const r = await fetch('http://localhost:8100/auth/discord', {
            method: "POST",
            body: JSON.stringify({code: search.get("code")})
        })
        if (!r.ok) {
            const data = await r.json()
            error = data.error || r.statusText
            return;
        }

        await getProfile();
        const redirect = temp.get("redirectUrl")
        window.location.href = redirect ? redirect : '/'
    })
</script>

{#if error != null}
    <Loader error={error as string} />
    <a href="/" title="Go back" class="underline fixed bottom-0 p-5 w-full text-center">Go Home</a>
{:else}
    <Loader />
{/if}