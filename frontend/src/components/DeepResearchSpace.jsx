import React from 'react';
import { Search, Info, Terminal, SearchCheck, XCircle, Loader2 } from 'lucide-react';

const DeepResearchSpace = ({ researchAnalysis, state }) => {
    const isThinking = state === 'thinking';
    const isComplete = state === 'complete';

    // Parse research analysis if it's JSON
    let data = null;
    try {
        if (researchAnalysis) {
            // Find JSON content within potential markdown blocks
            const jsonMatch = researchAnalysis.match(/\{[\s\S]*\}/);
            const jsonString = jsonMatch ? jsonMatch[0] : researchAnalysis;
            data = JSON.parse(jsonString);
        }
    } catch (e) {
        console.error("Failed to parse research analysis", e);
    }

    if (state === 'idle') return null;

    return (
        <section className="mb-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                <Search className="w-5 h-5 text-blue-400" />
                Deep Research Phase
                {isThinking && <Loader2 className="w-4 h-4 text-blue-400 animate-spin ml-2" />}
            </h2>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Column: Thinking Trace */}
                <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl overflow-hidden flex flex-col">
                    <div className="px-5 py-3 border-b border-zinc-800 bg-zinc-900/60 flex items-center gap-2">
                        <Terminal className="w-4 h-4 text-zinc-400" />
                        <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Thinking Trace</span>
                    </div>
                    <div className="p-6 flex-1 text-zinc-300">
                        {isThinking ? (
                            <div className="space-y-4">
                                <div className="h-4 bg-zinc-800/50 rounded animate-pulse w-full" />
                                <div className="h-4 bg-zinc-800/50 rounded animate-pulse w-5/6" />
                                <div className="h-4 bg-zinc-800/50 rounded animate-pulse w-4/6" />
                                <div className="h-4 bg-zinc-800/50 rounded animate-pulse w-full" />
                            </div>
                        ) : data?.thinking_trace ? (
                            <p className="text-sm leading-relaxed text-zinc-400 whitespace-pre-wrap font-mono italic">
                                "{data.thinking_trace}"
                            </p>
                        ) : (
                            <p className="text-zinc-500 italic text-sm">Identifying critical information gaps in the report...</p>
                        )}

                        {data?.confidence_gap && (
                            <div className="mt-6 p-4 bg-blue-900/10 border border-blue-800/20 rounded-xl">
                                <h4 className="text-xs font-bold text-blue-400 uppercase mb-2 flex items-center gap-2">
                                    <Info className="w-3 h-3" /> Minimum Confidence Gap
                                </h4>
                                <p className="text-sm text-zinc-300">{data.confidence_gap}</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Column: Search Results */}
                <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl overflow-hidden flex flex-col">
                    <div className="px-5 py-3 border-b border-zinc-800 bg-zinc-900/60 flex items-center gap-2">
                        <SearchCheck className="w-4 h-4 text-zinc-400" />
                        <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Active Search Queries</span>
                    </div>
                    <div className="p-6 flex-1 space-y-4">
                        {isThinking ? (
                            <div className="flex flex-col items-center justify-center h-full gap-4 py-12">
                                <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
                                <p className="text-zinc-500 text-sm animate-pulse">Formulating complex search strategies...</p>
                            </div>
                        ) : data?.search_queries?.length > 0 ? (
                            data.search_queries.map((item, idx) => (
                                <div key={idx} className="group p-4 bg-zinc-800/30 border border-zinc-700/50 rounded-xl transition-all hover:border-blue-500/30">
                                    <div className="flex items-start justify-between gap-4">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="text-[10px] font-bold px-1.5 py-0.5 bg-zinc-800 text-blue-400 border border-blue-900/30 rounded uppercase">
                                                    {item.topic}
                                                </span>
                                                <code className="text-[11px] text-zinc-500 font-mono">
                                                    "{item.query}"
                                                </code>
                                            </div>
                                            <p className="text-xs text-zinc-400 leading-relaxed mb-3">
                                                {item.rationale}
                                            </p>

                                            {item.result ? (
                                                <div className="p-3 bg-emerald-900/10 border border-emerald-800/20 rounded-lg">
                                                    <p className="text-xs text-emerald-400 leading-relaxed">
                                                        {item.result}
                                                    </p>
                                                </div>
                                            ) : (
                                                <div className="flex items-center gap-2 text-[10px] text-zinc-500">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                                                    Pending retrieval from web...
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="flex flex-col items-center justify-center h-full text-center py-12">
                                <XCircle className="w-10 h-10 text-zinc-800 mb-3" />
                                <p className="text-zinc-600 text-sm">No external information gaps identified for this report.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </section>
    );
};

export default DeepResearchSpace;
