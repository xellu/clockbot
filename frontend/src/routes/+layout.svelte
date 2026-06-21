<script lang="ts">

	import './layout.css';
	import favicon from '$lib/assets/favicon.png';

	import Loader from '$lib/components/Loader.svelte';
  
	import { onMount } from 'svelte';
	import { temp } from '$lib/scripts/Temp';
	import { CMS, type ContentType } from '$lib/stores/CMS';

	let { children } = $props();

	let error: boolean = $state(false);
	let loading: boolean = $state(true);
	let title: string = $state("Loading...");

	onMount(async () => {
		const cached = temp.get("cms")
		if (cached != null) {
			CMS.set(cached)
			loading = false

			title = cached.name;
			return
		}

		var r;
		try {
			r = await fetch(`http://localhost:8100/cms/branding`)
		} catch (e) {
			error = true
			return
		}

		if (!r.ok) {
			error = true
			return
		}

		const data = await r.json() as ContentType
		CMS.set(data)
		temp.set("cms", data)
		
		title = data.name;
		loading = false
	})
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>{title} | ClockBot</title>
</svelte:head>


{#if loading}

	<Loader error={error ? 'Page failed to load, please retry later.' : undefined} />

{:else}
	{@render children()}
{/if}