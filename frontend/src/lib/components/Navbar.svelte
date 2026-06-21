<script lang="ts">
    import Button from "./ui/button/button.svelte";

    import { CMS } from "$lib/stores/CMS";
</script>

<div class="fixed top-0 left-0 w-screen flex items-center justify-center p-3">
    <div class="max-w-6xl w-full flex items-center justify-between p-3 pl-5 bg-border/50 border border-border backdrop-blur-sm rounded-full">
        <a href="/">
            <h1 class="text-xl font-bold" style="color: {$CMS?.color};">{$CMS?.name}</h1>
        </a>

        <div class="flex items-center">
            <a href="/whitelist" title="Apply for Whitelist">
                <Button variant="outline" class="rounded-r-none">
                    Whitelist
                </Button>
            </a>
            <a href="{$CMS?.discordInvite}" title="Join our Discord" target="_blank">
                <Button variant="default" class="rounded-l-none" style="background-color: {$CMS?.color}">
                    Discord
                </Button>
            </a>
        </div>
    </div>
</div>