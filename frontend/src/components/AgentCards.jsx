import React, { useState } from 'react';
import {
    ShieldAlert,
    Heart,
    FileCheck,
    Loader2,
    CheckCircle2,
    AlertTriangle,
    Gavel,
    TrendingUp
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
    content,
    referenceContext,
    referenceQuery
}) {
    const isThinking = state === 'thinking';
    const isComplete = state === 'complete';
    const [showReference, setShowReference] = useState(false);

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
        yellow: {
            bg: 'bg-yellow-600',
            border: 'border-yellow-600/50',
            text: 'text-yellow-400',
            tag: 'bg-yellow-900/30 text-yellow-400'
        },
        purple: {
            bg: 'bg-purple-600',
            border: 'border-purple-600/50',
            text: 'text-purple-400',
            tag: 'bg-purple-900/30 text-purple-400'
        }
    };

    const colors = colorClasses[accentColor] || colorClasses.purple;

    // Utility: strip residual [C#...] citation markers from any string
    const stripCitations = (text) => {
        if (typeof text !== 'string') return text;
        return text.replace(/\[C#[^\]]*\]/g, '').trim();
    };

    // Recursively strip citations from all string values in an object
    const cleanData = (obj) => {
        if (typeof obj === 'string') return stripCitations(obj);
        if (Array.isArray(obj)) return obj.map(cleanData);
        if (obj && typeof obj === 'object') {
            return Object.fromEntries(
                Object.entries(obj).map(([k, v]) => [k, cleanData(v)])
            );
        }
        return obj;
    };

    // Severity badge component for consistent styling
    const SeverityBadge = ({ level, variant = 'default' }) => {
        const isHigh = level === 'High' || level === 'Critical';
        const baseClasses = 'text-[10px] px-2 py-0.5 rounded-md uppercase font-bold tracking-wider';
        const colorClasses = isHigh
            ? 'bg-red-900/50 text-red-300'
            : variant === 'yellow'
                ? 'bg-yellow-900/40 text-yellow-400'
                : 'bg-zinc-800 text-zinc-400';
        return <span className={`${baseClasses} ${colorClasses}`}>{level}</span>;
    };

    // Helper to render structured JSON content
    const renderContent = () => {
        if (!content) return null;

        try {
            if (content.trim().startsWith('{')) {
                const data = cleanData(JSON.parse(content));

                // 1. RISK AGENT RENDERING
                if (data.overall_risk_rating) {
                    return (
                        <div className="space-y-4">
                            <div className="flex flex-col gap-2 p-3 bg-zinc-800/50 rounded-lg border border-red-900/30">
                                <div className="flex justify-between items-center">
                                    <span className="text-zinc-400 text-xs uppercase tracking-wider">Overall Risk</span>
                                    <SeverityBadge level={data.overall_risk_rating} />
                                </div>
                                <div className="w-full bg-zinc-700 h-1.5 rounded-full mt-1">
                                    <div
                                        className="bg-red-500 h-1.5 rounded-full transition-all duration-500"
                                        style={{ width: `${(data.liquidity_score || 0.5) * 100}%` }}
                                    />
                                </div>
                            </div>

                            <div className="space-y-3">
                                {data.key_risk_factors?.map((rf, idx) => (
                                    <div key={idx} className="border-l-2 border-red-500/60 pl-3 py-1.5">
                                        <h4 className="text-sm font-medium text-zinc-200 mb-1">{rf.factor}</h4>
                                        <p className="text-xs text-zinc-400 leading-relaxed mb-1.5">{rf.impact}</p>
                                        {rf.evidence && (
                                            <p className="text-[11px] text-zinc-500 italic leading-relaxed">"{rf.evidence}"</p>
                                        )}
                                    </div>
                                ))}
                            </div>

                            {data.watchlist?.length > 0 && (
                                <div className="pt-3 border-t border-zinc-800">
                                    <h4 className="text-zinc-500 text-[10px] uppercase font-bold mb-2 tracking-wider">Watchlist</h4>
                                    <div className="flex flex-wrap gap-1.5">
                                        {data.watchlist.map((item, idx) => (
                                            <span key={idx} className="px-2 py-0.5 bg-zinc-800 text-zinc-400 text-[11px] rounded-md border border-zinc-700">
                                                {item}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                }

                // 2. BUSINESS OPS AGENT RENDERING
                if (data.capex_analysis) {
                    return (
                        <div className="space-y-4">
                            <div className="flex flex-col gap-2 p-3 bg-zinc-800/50 rounded-lg border border-yellow-900/30">
                                <div className="flex justify-between items-center">
                                    <span className="text-zinc-400 text-xs uppercase tracking-wider">Ops Risk Rating</span>
                                    <SeverityBadge level={data.operational_risk_rating} variant="yellow" />
                                </div>
                            </div>

                            <div className="space-y-3">
                                {data.capex_analysis && (
                                    <div className="border-l-2 border-yellow-500/60 pl-3 py-1.5">
                                        <h4 className="text-sm font-medium text-zinc-200 mb-1">
                                            CapEx Trend
                                            {data.capex_analysis.capex_trend && (
                                                <span className="text-zinc-500 font-normal text-xs ml-1">({data.capex_analysis.capex_trend})</span>
                                            )}
                                        </h4>
                                        <p className="text-xs text-zinc-400 leading-relaxed mb-1.5">{data.capex_analysis.risk_assessment}</p>
                                        {data.capex_analysis.evidence && (
                                            <p className="text-[11px] text-zinc-500 italic leading-relaxed">"{data.capex_analysis.evidence}"</p>
                                        )}
                                    </div>
                                )}

                                {data.key_business_risks?.map((risk, idx) => (
                                    <div key={idx} className="border-l-2 border-yellow-500/40 pl-3 py-1.5">
                                        <div className="flex items-center gap-2 mb-1">
                                            <SeverityBadge level={risk.severity} variant="yellow" />
                                            <h4 className="text-sm font-medium text-zinc-200">{risk.risk_type}</h4>
                                        </div>
                                        <p className="text-xs text-zinc-400 leading-relaxed mb-1.5">{risk.description}</p>
                                        {risk.evidence && (
                                            <p className="text-[11px] text-zinc-500 italic leading-relaxed">"{risk.evidence}"</p>
                                        )}
                                    </div>
                                ))}
                            </div>

                            {data.watchlist?.length > 0 && (
                                <div className="pt-3 border-t border-zinc-800">
                                    <h4 className="text-zinc-500 text-[10px] uppercase font-bold mb-2 tracking-wider">Watchlist</h4>
                                    <div className="flex flex-wrap gap-1.5">
                                        {data.watchlist.map((item, idx) => (
                                            <span key={idx} className="px-2 py-0.5 bg-zinc-800 text-zinc-400 text-[11px] rounded-md border border-zinc-700">
                                                {item}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                }

                // 3. GOVERNANCE AGENT RENDERING
                if (data.governance_risk_level) {
                    return (
                        <div className="space-y-4">
                            <div className="flex flex-col gap-2 p-3 bg-zinc-800/50 rounded-lg border border-purple-900/30">
                                <div className="flex justify-between items-center">
                                    <span className="text-zinc-400 text-xs uppercase tracking-wider">Governance Risk</span>
                                    <SeverityBadge level={data.governance_risk_level} />
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-zinc-400 text-xs uppercase tracking-wider">Compliance Risk</span>
                                    <SeverityBadge level={data.compliance_risk_level} />
                                </div>
                            </div>

                            <div className="space-y-3">
                                {data.key_findings?.map((finding, idx) => (
                                    <div key={idx} className="border-l-2 border-purple-500/60 pl-3 py-1.5">
                                        <div className="flex items-center gap-2 mb-1">
                                            <SeverityBadge level={finding.severity} />
                                            <h4 className="text-sm font-medium text-zinc-200">{finding.issue}</h4>
                                        </div>
                                        <p className="text-xs text-zinc-400 leading-relaxed mb-1.5">{finding.impact}</p>
                                        {finding.evidence && (
                                            <p className="text-[11px] text-zinc-500 italic leading-relaxed">"{finding.evidence}"</p>
                                        )}
                                    </div>
                                ))}
                            </div>

                            {data.non_disclosures?.length > 0 && (
                                <div className="pt-3 border-t border-zinc-800">
                                    <h4 className="text-zinc-500 text-[10px] uppercase font-bold mb-2 tracking-wider">Non-Disclosures</h4>
                                    <ul className="space-y-1">
                                        {data.non_disclosures.map((item, idx) => (
                                            <li key={idx} className="text-xs text-zinc-400 flex items-start gap-1.5">
                                                <span className="text-zinc-600 mt-0.5">•</span>
                                                <span>{item}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {data.limitations && (
                                <div className="pt-3 border-t border-zinc-800">
                                    <h4 className="text-zinc-500 text-[10px] uppercase font-bold mb-1 tracking-wider">Limitations</h4>
                                    <p className="text-xs text-zinc-400 leading-relaxed">{data.limitations}</p>
                                </div>
                            )}
                        </div>
                    );
                }

                // Generic findings fallback
                if (data.findings && typeof data.findings === 'object') {
                    const entries = Object.entries(data.findings);
                    const formatLabel = (value) => value
                        .replace(/[_-]+/g, ' ')
                        .replace(/\b\w/g, (char) => char.toUpperCase());

                    return (
                        <div className="space-y-3">
                            {entries.map(([key, value], idx) => {
                                const status = value?.status || 'Unknown';
                                const changes = Array.isArray(value?.changes)
                                    ? value.changes
                                    : (value?.changes ? [value.changes] : []);

                                return (
                                    <div key={idx} className="border-l-2 border-indigo-500/60 pl-3 py-1.5">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-[10px] px-2 py-0.5 rounded-md uppercase font-bold tracking-wider bg-indigo-900/50 text-indigo-300">
                                                {formatLabel(key)}
                                            </span>
                                            <span className="text-xs text-zinc-300">{status}</span>
                                        </div>
                                        {changes.length > 0 && (
                                            <ul className="space-y-1">
                                                {changes.slice(0, 3).map((item, changeIdx) => (
                                                    <li key={changeIdx} className="text-xs text-zinc-400 flex items-start gap-1.5">
                                                        <span className="text-zinc-600 mt-0.5">•</span>
                                                        <span>{item}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    );
                }
            }
        } catch (e) {
            // Fall back to markdown
        }

        return <ReactMarkdown>{stripCitations(content)}</ReactMarkdown>;
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
                                    <div className="mt-2 text-xs text-zinc-300 bg-zinc-950/60 border border-zinc-800 rounded p-3 max-h-48 overflow-y-auto whitespace-pre-wrap">
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
