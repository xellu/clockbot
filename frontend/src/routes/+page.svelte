<script lang="ts">
	import Navbar from '$lib/components/Navbar.svelte';
	import Footer from '$lib/components/Footer.svelte';
    import Button from '$lib/components/ui/button/button.svelte';
    import background from "$lib/assets/background.png"

    import { HugeiconsIcon } from '@hugeicons/svelte';
    import { DiscordFreeIcons } from '@hugeicons/core-free-icons';

    import { CMS } from "$lib/stores/CMS";

    let ipCopied = $state(false);
</script>

<Navbar />

<div class="fixed w-screen h-screen -z-50 opacity-30 blur-xs bg-cover" style="background: url({background})"></div>

<div class="w-screen h-[95vh] flex items-center justify-center">
    <div class="max-w-6xl w-full flex flex-col items-center justify-center">
        <h2 class="text-3xl lg:text-7xl font-extrabold">{$CMS?.name}</h2>

        <div class="flex items-center gap-5 mt-5 max-sm:flex-col">
            <div class="bg-border border border-border p-1 pl-3 rounded-full flex items-center gap-2 max-sm:hidden">
                <p class=" select-all">{$CMS?.mcIp}</p>
                <Button class="w-20"
                    onclick={() => {
                        navigator.clipboard.writeText($CMS?.mcIp as string)
                        ipCopied = true;
                        setTimeout(() => { ipCopied = false}, 1000)
                    }}
                >{ipCopied ? 'Copied' : 'Copy'}</Button>
            </div>

            <a href="{$CMS?.discordInvite}" target="_blank" title="Join Discord" class="flex gap-3 hover:underline">
                <HugeiconsIcon icon={DiscordFreeIcons} />
                <p>Discord</p>
            </a>
        </div>
    </div>
</div>

<Footer />
