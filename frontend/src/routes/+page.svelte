<script>
  import { onMount, onDestroy } from 'svelte';
  import { GraphView, typeColor } from '$lib/GraphView.js';

  let canvas = $state(null);
  let view = $state(null);
  let loading = $state(true);
  let error = $state('');
  let data = $state(null);

  let activeTypes = $state(new Set());
  let activeRanks = $state(new Set());
  let activeChakras = $state(new Set());
  let searchQuery = $state('');
  let selectedNode = $state(null);
  let showFilters = $state(false);

  let anyFilter = $derived(
    activeTypes.size > 0 || activeRanks.size > 0 || activeChakras.size > 0 || searchQuery.length >= 2,
  );

  let typeDistribution = $derived(data?.stats?.type_distribution ?? {});
  let allRanks = $derived([...(data?.stats?.all_ranks ?? []), 'None']);
  let allChakras = $derived(data?.stats?.all_chakras ?? []);
  let totalJutsus = $derived(data?.stats?.total_jutsus ?? 0);
  let totalTypes = $derived(data?.stats?.total_types ?? 0);

  let relatedNodes = $derived.by(() => {
    if (!view || !selectedNode || selectedNode.type !== 'jutsu') return [];
    return (view.edgesByNodeId[selectedNode.id] ?? [])
      .filter((e) => e.rel !== 'type_membership')
      .slice(0, 8)
      .map((e) => {
        const otherId = e.source === selectedNode.id ? e.target : e.source;
        const other = view.nodeById[otherId];
        return { node: other, dir: e.source === selectedNode.id ? '→' : '←', rel: e.rel };
      })
      .filter((r) => r.node);
  });

  onMount(async () => {
    try {
      const res = await fetch('/api/graph');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      data = await res.json();
      view = new GraphView(canvas, data, { onSelect: (n) => (selectedNode = n) });
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  });

  onDestroy(() => view?.destroy());

  $effect(() => {
    view?.setFilters({ activeTypes, activeRanks, activeChakras, searchQuery });
  });

  function toggle(set, val) {
    const next = new Set(set);
    next.has(val) ? next.delete(val) : next.add(val);
    return next;
  }

  function clearFilters() {
    activeTypes = new Set();
    activeRanks = new Set();
    activeChakras = new Set();
    searchQuery = '';
  }

  function focusType(typeName) {
    if (!view) return;
    const node = view.nodes.find((n) => n.type === 'category' && n.label === typeName);
    if (node) view.select(node);
  }

  function focusNode(node) {
    if (view && node) view.select(node);
  }
</script>

<div class="relative h-screen w-screen overflow-hidden bg-[#050510]">
  <canvas
    bind:this={canvas}
    class="absolute inset-0 h-full w-full cursor-grab active:cursor-grabbing"
  />

  <header
    class="pointer-events-none absolute top-0 right-0 left-0 flex items-center gap-3 px-5 py-3"
    style="background: linear-gradient(to bottom, rgba(5,5,16,0.9) 0%, transparent 100%)"
  >
    <h1 class="pointer-events-auto select-none text-lg font-bold text-orange-400">
      🍥 Naruto Jutsu Graph
    </h1>
    <span class="select-none text-xs text-gray-600">{totalJutsus} jutsus · {totalTypes} types</span>

    <div class="pointer-events-auto ml-auto flex items-center gap-2">
      <input
        bind:value={searchQuery}
        type="text"
        placeholder="Search…"
        class="w-44 rounded-full border border-white/10 bg-black/60 px-4 py-1.5 text-sm text-white outline-none placeholder:text-gray-600 transition-all duration-150 focus:border-orange-500/60 focus:bg-black/80 focus:w-56"
      />
      <button
        onclick={() => (showFilters = !showFilters)}
        class={[
          'rounded-full border px-3 py-1.5 text-xs transition-all duration-150 active:scale-95',
          showFilters || anyFilter
            ? 'border-orange-500 bg-orange-500/10 text-orange-400 hover:bg-orange-500/20'
            : 'border-white/10 text-gray-500 hover:border-orange-500/40 hover:text-gray-200',
        ].join(' ')}
      >{anyFilter ? '● Filter' : 'Filter'}</button>
    </div>
  </header>

  {#if showFilters}
    <aside
      class="absolute top-14 right-5 z-20 max-h-[75vh] w-60 overflow-y-auto rounded-xl border border-white/10 bg-[#080818]/95 p-4 shadow-2xl backdrop-blur"
    >
      <div class="mb-1 flex items-center justify-between">
        <span class="text-xs font-semibold uppercase tracking-widest text-orange-500">Filters</span>
        {#if anyFilter}
          <button
            onclick={clearFilters}
            class="rounded px-1.5 py-0.5 text-xs text-gray-500 transition-all duration-150 hover:bg-white/5 hover:text-white active:scale-95"
          >Clear</button>
        {/if}
      </div>

      <div class="mt-3 mb-1 text-[0.65rem] font-semibold uppercase tracking-widest text-gray-600">Type</div>
      <div class="flex flex-wrap gap-1">
        {#each Object.keys(typeDistribution) as t}
          <button
            onclick={() => (activeTypes = toggle(activeTypes, t))}
            class="rounded-full border px-2 py-0.5 text-[0.62rem] transition-all duration-150 active:scale-95"
            style="border-color:{activeTypes.has(t) ? typeColor(t) : '#333'}; background:{activeTypes.has(t) ? typeColor(t) + '25' : 'transparent'}; color:{activeTypes.has(t) ? '#fff' : '#777'}"
          >{t}</button>
        {/each}
      </div>

      {#if allRanks.length > 1}
        <div class="mt-3 mb-1 text-[0.65rem] font-semibold uppercase tracking-widest text-gray-600">Rank</div>
        <div class="flex flex-wrap gap-1">
          {#each allRanks as r}
            <button
              onclick={() => (activeRanks = toggle(activeRanks, r))}
              class={[
                'rounded-full border px-2 py-0.5 text-[0.62rem] transition-all duration-150 active:scale-95',
                activeRanks.has(r)
                  ? 'border-orange-500 bg-orange-500/20 text-white'
                  : 'border-gray-700 text-gray-500 hover:border-orange-500/40 hover:text-gray-300',
              ].join(' ')}
            >{r === 'None' ? 'Unranked' : `${r}-rank`}</button>
          {/each}
        </div>
      {/if}

      {#if allChakras.length}
        <div class="mt-3 mb-1 text-[0.65rem] font-semibold uppercase tracking-widest text-gray-600">Chakra</div>
        <div class="flex flex-wrap gap-1">
          {#each allChakras as c}
            <button
              onclick={() => (activeChakras = toggle(activeChakras, c))}
              class={[
                'rounded-full border px-2 py-0.5 text-[0.62rem] transition-all duration-150 active:scale-95',
                activeChakras.has(c)
                  ? 'border-cyan-400 bg-cyan-400/15 text-white'
                  : 'border-gray-700 text-gray-500 hover:border-cyan-500/40 hover:text-gray-300',
              ].join(' ')}
            >{c}</button>
          {/each}
        </div>
      {/if}

      <div class="mt-4 border-t border-white/5 pt-3 text-[0.65rem] font-semibold uppercase tracking-widest text-gray-600">Legend</div>
      <div class="mt-2 space-y-0.5">
        {#each Object.entries(typeDistribution) as [type, count]}
          <button
            onclick={() => { focusType(type); showFilters = false; }}
            class="flex w-full items-center gap-2 rounded px-1 py-0.5 transition-all duration-150 hover:bg-white/5 hover:translate-x-0.5 active:scale-[0.98]"
          >
            <span
              class="size-2 shrink-0 rounded-full transition-all duration-150"
              style="background:{typeColor(type)}; box-shadow:0 0 4px {typeColor(type)}"
            ></span>
            <span class="flex-1 text-left text-[0.72rem] text-gray-400 group-hover:text-gray-200">{type}</span>
            <span class="text-[0.65rem] text-gray-600">{count}</span>
          </button>
        {/each}
      </div>
    </aside>
  {/if}

  {#if selectedNode}
    <aside
      class="absolute top-14 right-5 z-10 w-72 overflow-y-auto rounded-xl border border-white/10 bg-[#080818]/95 p-4 shadow-2xl backdrop-blur"
      style="max-height: calc(100vh - 80px)"
    >
      <button
        onclick={() => view?.select(null)}
        class="absolute top-3 right-3 flex size-5 items-center justify-center rounded-full text-gray-600 transition-all duration-150 hover:bg-white/10 hover:text-white active:scale-90"
      >✕</button>

      <p class="mb-2 pr-4 text-base font-semibold leading-snug text-white">{selectedNode.label}</p>

      <div class="mb-3 flex flex-wrap gap-1">
        {#if selectedNode.type === 'category'}
          <span class="rounded-full border border-gray-600 px-2 py-0.5 text-[0.65rem] text-gray-400">
            {selectedNode.count} jutsus
          </span>
        {:else}
          {#each selectedNode.jutsu_types ?? [] as t}
            <button
              onclick={() => focusType(t)}
              class="rounded-full border px-2 py-0.5 text-[0.65rem] text-gray-300 transition-all duration-150 hover:text-white hover:brightness-125 active:scale-95"
              style="border-color:{typeColor(t)}60; background:{typeColor(t)}10"
            >{t}</button>
          {/each}
          {#if selectedNode.rank}
            <span class="rounded-full border border-yellow-500/40 px-2 py-0.5 text-[0.65rem] text-yellow-300">
              {selectedNode.rank}-rank
            </span>
          {/if}
          {#each selectedNode.chakra_natures ?? [] as c}
            <span class="rounded-full border border-cyan-500/40 px-2 py-0.5 text-[0.65rem] text-cyan-300">{c}</span>
          {/each}
        {/if}
      </div>

      <p class="text-[0.75rem] leading-relaxed text-gray-500">
        {selectedNode.full_description || selectedNode.description || 'No description.'}
      </p>

      {#if relatedNodes.length}
        <div class="mt-3 border-t border-white/5 pt-2">
          <p class="mb-1 text-[0.65rem] font-semibold uppercase tracking-widest text-gray-600">Related</p>
          {#each relatedNodes as { node, dir, rel }}
            <button
              onclick={() => focusNode(node)}
              class="block w-full rounded px-1 py-0.5 text-left text-[0.72rem] text-gray-500 transition-all duration-150 hover:bg-white/5 hover:translate-x-0.5 hover:text-yellow-300 active:scale-[0.98]"
            >
              <span class="mr-1 text-gray-700">{dir} {rel === 'derived_from' ? 'derived' : 'similar'}</span>
              {node.label}
            </button>
          {/each}
        </div>
      {/if}
    </aside>
  {/if}

  <div class="absolute bottom-5 left-5 flex gap-1.5">
    {#each [['Fit', () => view?.fit(true, true)], ['+', () => view?.zoom(1.4)], ['−', () => view?.zoom(0.7)], ['⚄', () => view?.jumpRandom()]] as [label, fn]}
      <button
        onclick={fn}
        class="rounded-lg border border-white/10 bg-black/70 px-3 py-1.5 text-xs text-gray-500 backdrop-blur transition-all duration-150 hover:border-orange-500/50 hover:bg-orange-500/5 hover:text-white active:scale-95"
      >{label}</button>
    {/each}
  </div>

  <p class="absolute right-5 bottom-5 select-none text-xs text-gray-700">scroll · drag · click</p>

  {#if loading}
    <div class="absolute inset-0 z-50 flex items-center justify-center bg-[#050510]">
      <p class="text-xl text-orange-500">{error ? `Error: ${error}` : 'Loading…'}</p>
    </div>
  {/if}
</div>
