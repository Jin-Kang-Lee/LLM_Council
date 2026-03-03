import React from 'react';
import {
    ShieldAlert,
    Heart,
    FileCheck,
    Loader2,
    CheckCircle2,
    AlertTriangle,
    Gavel
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

function ThinkingIndicator() {
    return (
        <div className="flex items-center gap-3 text-zinc-400">
            <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <span className="text-sm">Analyzing...</span>
        </div>
    );
}

function AgentCard({
    title,
    icon: Icon,
    accentColor,
    state,
    content
}) {
    const isThinking = state === 'thinking';
    const isComplete = state === 'complete';

    const colorClasses = {
        red: {
            bg: 'bg-red-600',
            border: 'border-red-600/50',
            text: 'text-red-400',
            tag: 'bg-red-900/30 text-red-400'
        },
        green: {
            bg: 'bg-emerald-600',
            border: 'border-emerald-600/50',
            text: 'text-emerald-400',
            tag: 'bg-emerald-900/30 text-emerald-400'
        },
        purple: {
            bg: 'bg-purple-600',
            border: 'border-purple-600/50',
            text: 'text-purple-400',
            tag: 'bg-purple-900/30 text-purple-400'
        }
    };

    const colors = colorClasses[accentColor] || colorClasses.purple;

    // Helper to render structured JSON content
    const renderContent = () => {
        if (!content) return null;

        try {
            // Check if content is JSON
            if (content.trim().startsWith('{')) {
                const data = JSON.parse(content);

                // 1. RISK AGENT RENDERING
                if (data.overall_risk_rating) {
                    return (
                        <div className="space-y-4">
                            <div className="flex flex-col gap-2 p-3 bg-zinc-800/50 rounded-lg border border-red-900/30">
                                <div className="flex justify-between items-center">
                                    <span className="text-zinc-400 text-xs uppercase tracking-wider">Overall Risk</span>
                                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${data.overall_risk_rating === 'High' || data.overall_risk_rating === 'Critical' ? 'bg-red-600 text-white' : 'bg-zinc-700 text-zinc-300'}`}>
                                        {data.overall_risk_rating}
                                    </span>
                                </div>
                                <div className="w-full bg-zinc-700 h-1.5 rounded-full mt-1">
                                    <div
                                        className="bg-red-500 h-1.5 rounded-full"
                                        style={{ width: `${(data.liquidity_score || 0.5) * 100}%` }}
                                    />
                                </div>
                            </div>

                            <div className="space-y-3">
                                {data.key_risk_factors?.map((rf, idx) => (
                                    <div key={idx} className="border-l-2 border-red-500 pl-3 py-1">
                                        <h4 className="text-zinc-200 font-medium text-xs mb-1">{rf.factor}</h4>
                                        <p className="text-zinc-400 text-[11px] mb-1">{rf.impact}</p>
                                        <p className="text-zinc-500 text-[10px] italic">"{rf.evidence}"</p>
                                    </div>
                                ))}
                            </div>

                            {data.watchlist?.length > 0 && (
                                <div className="pt-2 border-t border-zinc-800">
                                    <h4 className="text-red-400/70 text-[10px] uppercase font-bold mb-2 tracking-tighter">Watchlist Indicators</h4>
                                    <div className="flex flex-wrap gap-1">
                                        {data.watchlist.map((item, idx) => (
                                            <span key={idx} className="px-1.5 py-0.5 bg-zinc-800 text-zinc-400 text-[10px] rounded border border-zinc-700">
                                                {item}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                }

                // 2. SENTIMENT AGENT RENDERING
                if (data.overall_sentiment_score) {
                    return (
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-2">
                                <div className="p-2 bg-zinc-800/50 rounded border border-emerald-900/20 text-center">
                                    <p className="text-[10px] text-zinc-500 uppercase">Confidence</p>
                                    <p className="text-xs font-bold text-emerald-400">{data.executive_confidence}</p>
                                </div>
                                <div className="p-2 bg-zinc-800/50 rounded border border-emerald-900/20 text-center">
                                    <p className="text-[10px] text-zinc-500 uppercase">Outlook</p>
                                    <p className="text-xs font-bold text-emerald-400">{data.forward_outlook}</p>
                                </div>
                            </div>

                            <div className="space-y-3">
                                {data.key_signals?.map((sig, idx) => (
                                    <div key={idx} className="bg-zinc-800/30 p-2 rounded border border-zinc-700/50">
                                        <div className="flex items-center justify-between mb-1">
                                            <h4 className="text-zinc-200 font-medium text-xs">{sig.signal}</h4>
                                            <span className={`text-[9px] px-1 rounded ${sig.sentiment === 'Positive' ? 'text-emerald-400' : 'text-red-400'}`}>
                                                {sig.sentiment}
                                            </span>
                                        </div>
                                        <p className="text-zinc-400 text-[11px] font-light leading-snug">"{sig.evidence}"</p>
                                    </div>
                                ))}
                            </div>

                            <div className="pt-2">
                                <p className="text-center text-xs font-medium text-emerald-400 py-1 bg-emerald-500/10 rounded-full border border-emerald-500/20">
                                    Score: {data.overall_sentiment_score}
                                </p>
                            </div>
                        </div>
                    );
                }

                // 3. GOVERNANCE AGENT RENDERING
                if (data.governance_risk_level) {
                    return (
                        <div className="space-y-4">
                            <div className="flex flex-col gap-2 p-3 bg-zinc-800/50 rounded-lg border border-zinc-700">
                                <div className="flex justify-between items-center">
                                    <span className="text-zinc-400 text-xs uppercase tracking-wider">Gov Risk</span>
                                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${data.governance_risk_level === 'High' ? 'bg-red-600 text-white' : 'bg-zinc-700 text-zinc-300'}`}>
                                        {data.governance_risk_level}
                                    </span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-zinc-400 text-xs uppercase tracking-wider">Comp Risk</span>
                                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${data.compliance_risk_level === 'High' ? 'bg-red-600 text-white' : 'bg-zinc-700 text-zinc-300'}`}>
                                        {data.compliance_risk_level}
                                    </span>
                                </div>
                            </div>

                            <div className="space-y-3">
                                {data.key_findings?.map((finding, idx) => (
                                    <div key={idx} className="border-l-2 border-indigo-500 pl-3 py-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase font-bold ${finding.severity === 'High' ? 'bg-red-900/50 text-red-300' : 'bg-zinc-800 text-zinc-400'}`}>
                                                {finding.category}
                                            </span>
                                            <h4 className="text-zinc-200 font-medium text-xs">{finding.issue}</h4>
                                        </div>
                                        <p className="text-zinc-400 text-[11px] italic mb-1">"{finding.evidence}"</p>
                                        <p className="text-zinc-300 text-[11px] leading-relaxed">{finding.impact}</p>
                                    </div>
                                ))}
                            </div>

                            {data.non_disclosures?.length > 0 && (
                                <div className="pt-2 border-t border-zinc-800">
                                    <h4 className="text-zinc-500 text-[10px] uppercase font-bold mb-2">Non-Disclosures</h4>
                                    <ul className="list-disc list-inside text-[11px] text-zinc-400 space-y-1">
                                        {data.non_disclosures.slice(0, 3).map((item, idx) => (
                                            <li key={idx}>{item}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    );
                }
            }
        } catch (e) {
            // Fall back to markdown
        }

        return <ReactMarkdown>{content}</ReactMarkdown>;
    };

    return (
        <div className={`
      bg-zinc-900/50 border rounded-xl overflow-hidden transition-all duration-300
      ${isComplete ? colors.border : 'border-zinc-800'}
    `}>
            {/* Header */}
            <div className="px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg ${colors.bg} flex items-center justify-center`}>
                        <Icon className="w-4 h-4 text-white" />
                    </div>
                    <h3 className="font-medium text-zinc-200">{title}</h3>
                </div>

                <div className="flex items-center gap-2">
                    {isThinking && <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />}
                    {isComplete && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                </div>
            </div>

            {/* Content */}
            <div className="p-4 min-h-[200px] max-h-[400px] overflow-y-auto">
                {state === 'idle' && (
                    <div className="flex flex-col items-center justify-center h-full text-center py-8">
                        <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center mb-3">
                            <Icon className="w-5 h-5 text-zinc-500" />
                        </div>
                        <p className="text-zinc-500 text-sm">Waiting for content...</p>
                    </div>
                )}

                {isThinking && (
                    <div className="flex flex-col items-center justify-center h-full py-8">
                        <ThinkingIndicator />
                        <div className="mt-4 w-full space-y-3">
                            <div className="h-4 bg-zinc-800 rounded shimmer" />
                            <div className="h-4 bg-zinc-800 rounded w-3/4 shimmer" />
                            <div className="h-4 bg-zinc-800 rounded w-5/6 shimmer" />
                        </div>
                    </div>
                )}

                {isComplete && content && (
                    <div className="prose-custom text-sm">
                        {renderContent()}
                    </div>
                )}
            </div>
        </div>
    );
}

function ParserCard({ state, parsedContent }) {
    return (
        <div className={`
      bg-zinc-900/50 border rounded-xl overflow-hidden transition-all duration-300
      ${state === 'complete' ? 'border-indigo-600/50' : 'border-zinc-800'}
    `}>
            {/* Header */}
            <div className="px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
                        <FileCheck className="w-4 h-4 text-white" />
                    </div>
                    <h3 className="font-medium text-zinc-200">Parser Status</h3>
                </div>

                <div className="flex items-center gap-2">
                    {state === 'thinking' && <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />}
                    {state === 'complete' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                    {state === 'error' && <AlertTriangle className="w-4 h-4 text-red-400" />}
                </div>
            </div>

            {/* Content */}
            <div className="p-4 min-h-[200px] max-h-[400px] overflow-y-auto">
                {state === 'idle' && (
                    <div className="flex flex-col items-center justify-center h-full text-center py-8">
                        <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center mb-3">
                            <FileCheck className="w-5 h-5 text-zinc-500" />
                        </div>
                        <p className="text-zinc-500 text-sm">Waiting for input...</p>
                    </div>
                )}

                {state === 'thinking' && (
                    <div className="flex flex-col items-center justify-center h-full py-8">
                        <ThinkingIndicator />
                    </div>
                )}

                {state === 'complete' && parsedContent && (
                    <div className="space-y-4 text-sm">
                        <div className="flex items-center justify-between">
                            <span className="text-zinc-500">Word Count</span>
                            <span className="text-zinc-300 font-medium">{parsedContent.word_count}</span>
                        </div>

                        {parsedContent.sections_identified?.length > 0 && (
                            <div>
                                <p className="text-zinc-500 mb-2">Identified Topics</p>
                                <div className="flex flex-wrap gap-2">
                                    {parsedContent.sections_identified.map((section, idx) => (
                                        <span
                                            key={idx}
                                            className="px-2 py-1 bg-zinc-800 text-zinc-300 text-xs rounded-full"
                                        >
                                            {section}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className="pt-2 border-t border-zinc-800">
                            <p className="text-emerald-400 flex items-center gap-2">
                                <CheckCircle2 className="w-4 h-4" />
                                Content parsed successfully
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

function AgentCards({
    riskAnalysis,
    sentimentAnalysis,
    governanceAnalysis,
    riskState,
    sentimentState,
    governanceState,
    parserState,
    parsedContent
}) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <ParserCard state={parserState} parsedContent={parsedContent} />

            <AgentCard
                title="Risk Analyst"
                icon={ShieldAlert}
                accentColor="red"
                state={riskState}
                content={riskAnalysis}
            />

            <AgentCard
                title="Sentiment Analyst"
                icon={Heart}
                accentColor="green"
                state={sentimentState}
                content={sentimentAnalysis}
            />

            <AgentCard
                title="Governance Analyst"
                icon={Gavel}
                accentColor="purple"
                state={governanceState}
                content={governanceAnalysis}
            />
        </div>
    );
}

export default AgentCards;
