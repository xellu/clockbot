<script lang="ts">
    import Button from "$lib/components/ui/button/button.svelte";
    
    import { CMS } from "$lib/stores/CMS";
    import { temp } from "$lib/scripts/Temp";
    import { DiscordIcon } from "@hugeicons/core-free-icons";
    import { HugeiconsIcon } from "@hugeicons/svelte";
    
    import { Account } from "$lib/stores/Account";
</script>

{#if $Account == null}
<div class="w-screen h-screen flex items-center justify-center">
    <div>
        <h1 class="font-semibold uppercase text-xs mb-1">Admin Panel</h1>    
        <Button style="background-color: #5865f2; color: white;" onclick={() => {
            temp.set("redirectUrl", "/static/admin.html")
            window.location.href = `https://discord.com/oauth2/authorize?client_id=${$CMS?.discordClientId}&response_type=code&redirect_uri=${encodeURIComponent($CMS?.domain + '/static/auth.html')}&scope=identify`
        }}>
            <HugeiconsIcon icon={DiscordIcon} /> Sign In with Discord
        </Button>
    </div>
</div>
{:else}
    <p>{$Account.discord}</p>
{/if}