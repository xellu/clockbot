<script lang="ts">
    import logo from "$lib/assets/logo.png";
    import Layer1 from "$lib/assets/loader_layer1.png"
    import Layer2 from "$lib/assets/loader_layer2.png"

    import { CMS } from "$lib/stores/CMS";
</script>

<style>
    #LINKS a:hover {
        color: white;
        text-decoration: underline;
        transition-duration: 100ms;
    }
</style>

<div class="w-screen border-t border-border flex items-center justify-center bg-background">
    <div class="max-w-6xl w-full flex justify-between p-5 pt-8 pb-16 max-md:flex-col-reverse max-md:items-center gap-10">
        <div class="max-w-64">
            <p class="font-bold uppercase text-sm">Powered by</p>
            <a href="https://github.com/xellu/clockbot" target="_blank">
                <img src="{logo}" alt="ClockBot" class="w-64 -mt-5" draggable="false">
            </a>
            <p class="text-xs -mt-3 text-chart-1">Developed at <a href="https://catboys.cc/" class="underline" target="_blank">Backtanked</a></p>

            {#if $CMS?.name.toLowerCase() == "backtanked"}
                <p class="mt-3 text-xs italic text-white/60">We developed ClockBot to make our lives easier. Try it for yourself!</p>
            {:else}
                <p class="mt-3 text-xs italic text-chart-2">This server uses the ClockBot system for whitelist management. ClockBot is not affiliated with "{$CMS?.name}"</p>
            {/if}
        </div>

        <a href="/" class="max-md:order-1 max-md:scale-200 max-md:-mt-20 self-center">
            <div class="flex flex-col select-none">
                <img src="{Layer1}" alt="Loading" class="w-24 animate-spin" style="animation-duration: 5s;" draggable="false">
                <img src="{Layer2}" alt="Loading" class="w-24 -mt-24 z-50" draggable="false">
            </div>
        </a>

        <div class="flex flex-col gap-1 w-64 text-white/60" id="LINKS">
            <h3 class="text-xl font-semibold text-white">Links</h3>

            <a href="{$CMS?.discordInvite}" target="_blank">Discord Server</a>
            <a href="/whitelist">Get Whitelisted</a>
            <a href="https://github.com/xellu/clockbot" target="_blank" class="mt-3 italic" style="color: {$CMS?.color}">Try ClockBot</a>
        </div>
    </div>
</div>