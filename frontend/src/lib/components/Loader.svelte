<script lang="ts">
    import { onMount } from "svelte";
    import { slide } from "svelte/transition";

    import Layer1 from "$lib/assets/loader_layer1.png"
    import Layer2 from "$lib/assets/loader_layer2.png"

    let timeout: boolean = $state(false);
    
    let { error }: {error?: string} = $props();

    onMount(() => {
        setTimeout(() => {
            timeout = true;
        }, 5000)
    })
</script>

<div class="fixed w-screen h-screen flex flex-col items-center justify-center select-none">
    <div class="flex text-7xl font-bold items-center">
        <p class="{error ? '' : 'animate-pulse'}">Cl</p>
        <div class="flex flex-col">
            <img src="{Layer1}" alt="Loading" class="w-16 animate-spin" style="animation-duration: 2s;" draggable="false">
            <img src="{Layer2}" alt="Loading" class="w-16 -mt-16 z-50" draggable="false">
        </div>
        <p class="{error ? '' : 'animate-pulse'}">ckBot</p>
    </div>

    {#if timeout}
        <p class="text-chart-2 {error ? 'hidden' : ''}" transition:slide>This is taking a while...</p>
    {/if}

    {#if error}
        <p class=" text-destructive" transition:slide>{error}</p>
    {/if}
</div>