<script lang="ts">
    import { CMS } from "$lib/stores/CMS";
    import { DiscordIcon } from "@hugeicons/core-free-icons";
    import { HugeiconsIcon } from "@hugeicons/svelte";

    import Button from "$lib/components/ui/button/button.svelte";
</script>

<div class="w-screen h-screen flex items-center justify-center">
    <div>
        <h1 class="font-semibold uppercase text-xs mb-1">Admin Panel</h1>
        <a href="https://discord.com/oauth2/authorize?client_id={$CMS?.discordClientId}&response_type=code&redirect_uri={encodeURIComponent($CMS?.domain + '/static/admin.html')}&scope=identify">
            <Button style="background-color: #5865f2; color: white;">
                <HugeiconsIcon icon={DiscordIcon} /> Sign In with Discord
            </Button>
        </a>
    </div>
</div>