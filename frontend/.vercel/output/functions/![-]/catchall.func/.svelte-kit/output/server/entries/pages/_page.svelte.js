import { n as onDestroy } from "../../chunks/index-server.js";
import { L as attr, R as clsx, a as ensure_array_like, i as derived, n as attr_class, z as escape_html } from "../../chunks/dev.js";
import "d3-force";
//#endregion
//#region src/routes/+page.svelte
function _page($$renderer, $$props) {
	$$renderer.component(($$renderer) => {
		let view = null;
		let data = null;
		let activeTypes = /* @__PURE__ */ new Set();
		let activeRanks = /* @__PURE__ */ new Set();
		let activeChakras = /* @__PURE__ */ new Set();
		let searchQuery = "";
		let anyFilter = derived(() => activeTypes.size > 0 || activeRanks.size > 0 || activeChakras.size > 0 || false);
		derived(() => data?.stats?.type_distribution ?? {});
		derived(() => [...data?.stats?.all_ranks ?? [], "None"]);
		derived(() => data?.stats?.all_chakras ?? []);
		let totalJutsus = derived(() => data?.stats?.total_jutsus ?? 0);
		let totalTypes = derived(() => data?.stats?.total_types ?? 0);
		derived(() => {
			return [];
		});
		onDestroy(() => view?.destroy());
		$$renderer.push(`<div class="relative h-screen w-screen overflow-hidden bg-[#050510]"><canvas class="absolute inset-0 h-full w-full cursor-grab active:cursor-grabbing"></canvas> <header class="pointer-events-none absolute top-0 right-0 left-0 flex items-center gap-3 px-5 py-3" style="background: linear-gradient(to bottom, rgba(5,5,16,0.9) 0%, transparent 100%)"><h1 class="pointer-events-auto select-none text-lg font-bold text-orange-400">🍥 Naruto Jutsu Graph</h1> <span class="select-none text-xs text-gray-600">${escape_html(totalJutsus())} jutsus · ${escape_html(totalTypes())} types</span> <div class="pointer-events-auto ml-auto flex items-center gap-2"><input${attr("value", searchQuery)} type="text" placeholder="Search…" class="w-44 rounded-full border border-white/10 bg-black/60 px-4 py-1.5 text-sm text-white outline-none placeholder:text-gray-600 transition-all duration-150 focus:border-orange-500/60 focus:bg-black/80 focus:w-56"/> <button${attr_class(clsx(["rounded-full border px-3 py-1.5 text-xs transition-all duration-150 active:scale-95", anyFilter() ? "border-orange-500 bg-orange-500/10 text-orange-400 hover:bg-orange-500/20" : "border-white/10 text-gray-500 hover:border-orange-500/40 hover:text-gray-200"].join(" ")))}>${escape_html(anyFilter() ? "● Filter" : "Filter")}</button></div></header> `);
		$$renderer.push("<!--[-1-->");
		$$renderer.push(`<!--]--> `);
		$$renderer.push("<!--[-1-->");
		$$renderer.push(`<!--]--> <div class="absolute bottom-5 left-5 flex gap-1.5"><!--[-->`);
		const each_array_7 = ensure_array_like([
			["Fit", () => view?.fit(true, true)],
			["+", () => view?.zoom(1.4)],
			["−", () => view?.zoom(.7)],
			["⚄", () => view?.jumpRandom()]
		]);
		for (let $$index_7 = 0, $$length = each_array_7.length; $$index_7 < $$length; $$index_7++) {
			let [label, fn] = each_array_7[$$index_7];
			$$renderer.push(`<button class="rounded-lg border border-white/10 bg-black/70 px-3 py-1.5 text-xs text-gray-500 backdrop-blur transition-all duration-150 hover:border-orange-500/50 hover:bg-orange-500/5 hover:text-white active:scale-95">${escape_html(label)}</button>`);
		}
		$$renderer.push(`<!--]--></div> <p class="absolute right-5 bottom-5 select-none text-xs text-gray-700">scroll · drag · click</p> `);
		$$renderer.push("<!--[0-->");
		$$renderer.push(`<div class="absolute inset-0 z-50 flex items-center justify-center bg-[#050510]"><p class="text-xl text-orange-500">${escape_html("Loading…")}</p></div>`);
		$$renderer.push(`<!--]--></div>`);
	});
}
//#endregion
export { _page as default };
