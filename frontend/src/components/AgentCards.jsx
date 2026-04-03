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
        red:    { bg: 'bg-red-600',    border: 'border-red-600/50'    },
        yellow: { bg: 'bg-yellow-600', border: 'border-yellow-600/50' },
        purple: { bg: 'bg-purple-600', border: 'border-purple-600/50' },
        indigo: { bg: 'bg-indigo-600', border: 'border-indigo-600/50' },
    };

    const colors = colorClasses[accentColor] || colorClasses.indigo;

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
                    <div className="prose-custom text-sm">
                        <ReactMarkdown>{content}</ReactMarkdown>

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
