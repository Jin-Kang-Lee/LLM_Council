import React, { useState } from 'react';
import {
    ShieldAlert,
    FileCheck,
    Loader2,
    CheckCircle2,
    AlertTriangle,
    Gavel,
    TrendingUp
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function tryParseJson(str) {
    if (!str || typeof str !== 'string') return null;
    const trimmed = str.trim();
    if (!trimmed.startsWith('{')) return null;
    try { return JSON.parse(trimmed); } catch { return null; }
}

function humanize(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

const SEVERITY_STYLES = {
    low:      'bg-emerald-900/40 text-emerald-300 border border-emerald-700/40',
    medium:   'bg-amber-900/40  text-amber-300  border border-amber-700/40',
    high:     'bg-red-900/40    text-red-300    border border-red-700/40',
    critical: 'bg-red-950/60   text-red-200    border border-red-600/50',
    bullish:  'bg-emerald-900/40 text-emerald-300 border border-emerald-700/40',
    neutral:  'bg-zinc-800     text-zinc-300   border border-zinc-600/40',
    bearish:  'bg-red-900/40    text-red-300    border border-red-700/40',
};

function SeverityBadge({ value }) {
    const key = (value || '').toLowerCase().split(' ')[0];
    const cls = SEVERITY_STYLES[key] || 'bg-zinc-800 text-zinc-300 border border-zinc-600/40';
    return (
        <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold ${cls}`}>
            {value}
        </span>
    );
}

function ScoreBar({ value }) {
    const pct = Math.round((value ?? 0) * 100);
    const color = pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-red-500';
    return (
        <div className="flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-zinc-700 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
            </div>
            <span className="text-xs text-zinc-400 w-8 text-right">{pct}%</span>
        </div>
    );
}

// ─── Generic JSON renderer for agent cards ────────────────────────────────────

const RATING_KEYS = new Set(['overall_risk_rating', 'operational_risk_rating', 'governance_risk_level', 'compliance_risk_level', 'capex_trend', 'severity', 'risk_level', 'market_outlook']);
const SCORE_KEYS  = new Set(['confidence_score', 'liquidity_score']);

function RenderValue({ fieldKey, value }) {
    if (RATING_KEYS.has(fieldKey)) return <SeverityBadge value={String(value)} />;
    if (SCORE_KEYS.has(fieldKey))  return <ScoreBar value={value} />;

    if (Array.isArray(value)) {
        if (value.length === 0) return <span className="text-zinc-500 text-xs">—</span>;
        if (typeof value[0] === 'string') {
            return (
                <ul className="mt-1 space-y-1">
                    {value.map((item, i) => (
                        <li key={i} className="flex gap-2 text-xs text-zinc-300">
                            <span className="text-zinc-500 mt-0.5">•</span>
                            <span>{item}</span>
                        </li>
                    ))}
                </ul>
            );
        }
        // Array of objects
        return (
            <div className="mt-1 space-y-2">
                {value.map((item, i) => (
                    <div key={i} className="bg-zinc-950/50 border border-zinc-800 rounded-lg p-2.5 space-y-1.5">
                        <RenderObject data={item} compact />
                    </div>
                ))}
            </div>
        );
    }

    if (value !== null && typeof value === 'object') {
        return (
            <div className="mt-1 bg-zinc-950/40 border border-zinc-800 rounded-lg p-2.5 space-y-1.5">
                <RenderObject data={value} compact />
            </div>
        );
    }

    return <span className="text-xs text-zinc-200 break-words">{String(value ?? '—')}</span>;
}

function RenderObject({ data, compact = false }) {
    return (
        <>
            {Object.entries(data).map(([key, val]) => {
                const isRating = RATING_KEYS.has(key);
                const isScore  = SCORE_KEYS.has(key);
                const isSimple = isRating || isScore || (typeof val !== 'object' && !Array.isArray(val));

                if (isSimple) {
                    return (
                        <div key={key} className={`flex items-center justify-between gap-3 ${compact ? '' : 'py-1'}`}>
                            <span className="text-xs text-zinc-500 shrink-0">{humanize(key)}</span>
                            <div className={isScore ? 'flex-1 max-w-[120px]' : ''}>
                                <RenderValue fieldKey={key} value={val} />
                            </div>
                        </div>
                    );
                }

                return (
                    <div key={key} className="pt-1">
                        <p className="text-xs text-zinc-500 mb-1">{humanize(key)}</p>
                        <RenderValue fieldKey={key} value={val} />
                    </div>
                );
            })}
        </>
    );
}

function AnalysisJsonRenderer({ data }) {
    // Pull top-level rating / score to a header summary
    const topRatingKey = Object.keys(data).find(k => RATING_KEYS.has(k));
    const topScoreKey  = Object.keys(data).find(k => SCORE_KEYS.has(k));

    return (
        <div className="space-y-3">
            {/* Summary strip */}
            {(topRatingKey || topScoreKey) && (
                <div className="flex items-center justify-between bg-zinc-950/60 border border-zinc-800 rounded-lg px-3 py-2">
                    {topRatingKey && (
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-zinc-500">Rating</span>
                            <SeverityBadge value={data[topRatingKey]} />
                        </div>
                    )}
                    {topScoreKey && (
                        <div className="flex items-center gap-2 min-w-[140px]">
                            <span className="text-xs text-zinc-500 shrink-0">Confidence</span>
                            <ScoreBar value={data[topScoreKey]} />
                        </div>
                    )}
                </div>
            )}

            {/* All remaining fields */}
            {Object.entries(data).map(([key, val]) => {
                if (key === topRatingKey || key === topScoreKey) return null;

                const isArray  = Array.isArray(val);
                const isObject = val !== null && typeof val === 'object' && !isArray;
                const isSimple = !isArray && !isObject;

                if (isSimple) {
                    return (
                        <div key={key} className="flex items-start justify-between gap-3">
                            <span className="text-xs text-zinc-500 shrink-0 pt-0.5">{humanize(key)}</span>
                            <RenderValue fieldKey={key} value={val} />
                        </div>
                    );
                }

                return (
                    <div key={key}>
                        <p className="text-xs font-semibold text-zinc-400 mb-1.5">{humanize(key)}</p>
                        <RenderValue fieldKey={key} value={val} />
                    </div>
                );
            })}
        </div>
    );
}

// ─── ThinkingIndicator ────────────────────────────────────────────────────────

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

// ─── AgentCard ────────────────────────────────────────────────────────────────

function AgentCard({ title, icon: Icon, accentColor, state, content, referenceContext, referenceQuery }) {
    const isThinking = state === 'thinking';
    const isComplete = state === 'complete';
    const [showReference, setShowReference] = useState(false);

    const colorClasses = {
        red:    { bg: 'bg-red-600',    border: 'border-red-600/50'    },
        yellow: { bg: 'bg-yellow-600', border: 'border-yellow-600/50' },
        purple: { bg: 'bg-purple-600', border: 'border-purple-600/50' },
        indigo: { bg: 'bg-indigo-600', border: 'border-indigo-600/50' },
    };
    const colors = colorClasses[accentColor] || colorClasses.indigo;

    const parsed = isComplete ? tryParseJson(content) : null;

    return (
        <div className={`bg-zinc-900/50 border rounded-xl overflow-hidden transition-all duration-300 ${isComplete ? colors.border : 'border-zinc-800'}`}>
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
                    <div className="text-sm">
                        {parsed
                            ? <AnalysisJsonRenderer data={parsed} />
                            : <div className="prose-custom"><ReactMarkdown>{content}</ReactMarkdown></div>
                        }

                        {referenceContext && (
                            <div className="mt-4 pt-3 border-t border-zinc-800">
                                <button
                                    type="button"
                                    onClick={() => setShowReference(prev => !prev)}
                                    className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                                >
                                    {showReference ? 'Hide' : 'Show'} Reference Context
                                </button>
                                {showReference && (
                                    <div className="mt-2 text-xs text-zinc-300 bg-zinc-950/60 border border-zinc-800 rounded p-3 max-h-48 overflow-y-auto">
                                        {referenceQuery && (
                                            <div className="text-zinc-500 mb-2">
                                                <span className="font-semibold">Query:</span> {referenceQuery}
                                            </div>
                                        )}
                                        <pre className="whitespace-pre-wrap font-sans">{referenceContext}</pre>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

// ─── ParserCard ───────────────────────────────────────────────────────────────

function ParserCard({ state, parsedContent }) {
    return (
        <div className={`bg-zinc-900/50 border rounded-xl overflow-hidden transition-all duration-300 ${state === 'complete' ? 'border-indigo-600/50' : 'border-zinc-800'}`}>
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
                    {state === 'error'    && <AlertTriangle className="w-4 h-4 text-red-400" />}
                </div>
            </div>

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
                                        <span key={idx} className="px-2 py-1 bg-zinc-800 text-zinc-300 text-xs rounded-full">
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

// ─── AgentCards (export) ──────────────────────────────────────────────────────

function AgentCards({
    riskAnalysis,
    businessOpsAnalysis,
    governanceAnalysis,
    riskState,
    businessOpsState,
    governanceState,
    parserState,
    parsedContent,
    riskReferenceContext,
    businessOpsReferenceContext,
    governanceReferenceContext,
    riskReferenceQuery,
    businessOpsReferenceQuery,
    governanceReferenceQuery
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
                referenceContext={riskReferenceContext}
                referenceQuery={riskReferenceQuery}
            />

            <AgentCard
                title="Business & Ops Analyst"
                icon={TrendingUp}
                accentColor="yellow"
                state={businessOpsState}
                content={businessOpsAnalysis}
                referenceContext={businessOpsReferenceContext}
                referenceQuery={businessOpsReferenceQuery}
            />

            <AgentCard
                title="Governance Analyst"
                icon={Gavel}
                accentColor="purple"
                state={governanceState}
                content={governanceAnalysis}
                referenceContext={governanceReferenceContext}
                referenceQuery={governanceReferenceQuery}
            />
        </div>
    );
}

export default AgentCards;
