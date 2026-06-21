<script lang="ts">
    import background from "$lib/assets/background.png"
    import Footer from "$lib/components/Footer.svelte";

    let details: {discord: number, minecraft: string} = {
        discord: 0,
        minecraft: ""
    }
</script>

<div class="fixed w-screen h-screen -z-50 opacity-30 blur-xs bg-cover" style="background: url({background})"></div>

<div class="min-h-screen w-screen flex items-center justify-center">

</div>

<Footer />