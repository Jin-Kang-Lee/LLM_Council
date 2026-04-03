import React from 'react';
import { FileText, Loader2, Download, Copy, CheckCircle2, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function tryParseJson(str) {
    if (!str || typeof str !== 'string') return null;
    const trimmed = str.trim();
    if (!trimmed.startsWith('{')) return null;
    try { return JSON.parse(trimmed); } catch { return null; }
}

const SEVERITY_STYLES = {
    low:         'bg-emerald-900/40 text-emerald-300 border border-emerald-700/40',
    medium:      'bg-amber-900/40  text-amber-300  border border-amber-700/40',
    high:        'bg-red-900/40    text-red-300    border border-red-700/40',
    critical:    'bg-red-950/60   text-red-200    border border-red-600/50',
    outperform:  'bg-emerald-900/40 text-emerald-300 border border-emerald-700/40',
    neutral:     'bg-zinc-800     text-zinc-300   border border-zinc-600/40',
    underperform:'bg-red-900/40    text-red-300    border border-red-700/40',
    bullish:     'bg-emerald-900/40 text-emerald-300 border border-emerald-700/40',
    bearish:     'bg-red-900/40    text-red-300    border border-red-700/40',
};

function Badge({ value, size = 'sm' }) {
    const key = (value || '').toLowerCase().split(' ')[0];
    const cls = SEVERITY_STYLES[key] || 'bg-zinc-800 text-zinc-300 border border-zinc-600/40';
    const padding = size === 'lg' ? 'px-3 py-1 text-sm' : 'px-2 py-0.5 text-xs';
    return (
        <span className={`inline-block rounded-full font-semibold ${padding} ${cls}`}>
            {value}
        </span>
    );
}

function ScoreBar({ value, label }) {
    const pct = Math.round((value ?? 0) * 100);
    const color = pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-red-500';
    return (
        <div className="flex items-center gap-3">
            {label && <span className="text-xs text-zinc-500 w-20 shrink-0">{label}</span>}
            <div className="flex-1 h-1.5 bg-zinc-700 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
            </div>
            <span className="text-xs text-zinc-400 w-8 text-right">{pct}%</span>
        </div>
    );
}

function Section({ title, children, className = '' }) {
    return (
        <div className={`space-y-2 ${className}`}>
            <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-500">{title}</h3>
            {children}
        </div>
    );
}

function Divider() {
    return <div className="border-t border-zinc-800" />;
}

// ─── Generic JSON fallback renderer ──────────────────────────────────────────

function humanize(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function GenericValue({ value }) {
    if (value === null || value === undefined) return <span className="text-zinc-500">—</span>;
    if (typeof value === 'boolean') return <span className="text-zinc-300">{String(value)}</span>;
    if (typeof value === 'number') return <span className="text-zinc-200">{value}</span>;

    if (Array.isArray(value)) {
        if (value.length === 0) return <span className="text-zinc-500">—</span>;
        if (typeof value[0] !== 'object') {
            return (
                <ul className="mt-1 space-y-1">
                    {value.map((item, i) => (
                        <li key={i} className="flex gap-2 text-xs text-zinc-300">
                            <span className="text-zinc-500 mt-0.5">•</span>{String(item)}
                        </li>
                    ))}
                </ul>
            );
        }
        return (
            <div className="mt-1 space-y-2">
                {value.map((item, i) => (
                    <div key={i} className="bg-zinc-950/50 border border-zinc-800 rounded-lg p-3">
                        <GenericObject data={item} />
                    </div>
                ))}
            </div>
        );
    }

    if (typeof value === 'object') {
        return (
            <div className="mt-1 bg-zinc-950/40 border border-zinc-800 rounded-lg p-3">
                <GenericObject data={value} />
            </div>
        );
    }

    return <span className="text-xs text-zinc-200 break-words">{String(value)}</span>;
}

function GenericObject({ data }) {
    return (
        <div className="space-y-2">
            {Object.entries(data).map(([key, val]) => {
                const isComplex = Array.isArray(val) || (val !== null && typeof val === 'object');
                return (
                    <div key={key} className={isComplex ? '' : 'flex items-start justify-between gap-4'}>
                        <span className="text-xs text-zinc-500 shrink-0">{humanize(key)}</span>
                        <div className={isComplex ? 'mt-1' : ''}>
                            <GenericValue value={val} />
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

function GenericJsonRenderer({ data }) {
    return (
        <div className="space-y-4">
            {Object.entries(data).map(([key, val]) => {
                const isComplex = Array.isArray(val) || (val !== null && typeof val === 'object');
                return (
                    <div key={key}>
                        <p className={`text-xs font-bold uppercase tracking-widest mb-2 ${isComplex ? 'text-zinc-500' : 'text-zinc-500'}`}>
                            {humanize(key)}
                        </p>
                        {isComplex ? (
                            <GenericValue value={val} />
                        ) : (
                            <p className="text-sm text-zinc-300 leading-relaxed">{String(val ?? '—')}</p>
                        )}
                    </div>
                );
            })}
        </div>
    );
}

// ─── Findings/Regulatory renderer (current master agent output) ───────────────

function FindingsReportRenderer({ data }) {
    const { report_name, date, findings, regulatory_requirements, regulatory_gaps, regulatory_gap_recommendations } = data;

    return (
        <div className="space-y-6 text-sm">

            {/* Header */}
            {(report_name || date) && (
                <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
                    <h2 className="text-base font-semibold text-zinc-200">{report_name || 'Analysis Report'}</h2>
                    {date && <span className="text-xs text-zinc-500">{date}</span>}
                </div>
            )}

            {/* Findings */}
            {findings?.length > 0 && (
                <div className="space-y-2">
                    <p className="text-xs font-bold uppercase tracking-widest text-zinc-500">Key Findings</p>
                    <div className="space-y-3">
                        {findings.map((f, i) => (
                            <div key={i} className="bg-zinc-950/50 border border-zinc-800 rounded-xl p-4 space-y-2">
                                <p className="text-sm font-semibold text-zinc-200">{f.issue}</p>
                                <p className="text-xs text-zinc-400 leading-relaxed">{f.description}</p>
                                {f.recommendation && (
                                    <div className="pt-2 border-t border-zinc-800">
                                        <p className="text-xs font-medium text-emerald-400 mb-1">Recommendation</p>
                                        <p className="text-xs text-zinc-300 leading-relaxed">{f.recommendation}</p>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Regulatory Requirements */}
            {regulatory_requirements?.length > 0 && (
                <div className="space-y-2">
                    <p className="text-xs font-bold uppercase tracking-widest text-zinc-500">Regulatory Requirements</p>
                    <div className="space-y-3">
                        {regulatory_requirements.map((r, i) => (
                            <div key={i} className="bg-zinc-950/50 border border-zinc-800 rounded-xl p-4 space-y-2">
                                <p className="text-sm font-semibold text-zinc-200">{r.requirement}</p>
                                <p className="text-xs text-zinc-400 leading-relaxed">{r.description}</p>
                                {r.gap && (
                                    <div className="flex gap-2 text-xs text-amber-300 bg-amber-950/30 border border-amber-800/30 rounded-lg p-2">
                                        <span className="font-medium shrink-0">Gap:</span>
                                        <span>{r.gap}</span>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Regulatory Gaps */}
            {regulatory_gaps?.length > 0 && (
                <div className="space-y-2">
                    <p className="text-xs font-bold uppercase tracking-widest text-zinc-500">Regulatory Gaps</p>
                    <div className="space-y-3">
                        {regulatory_gaps.map((g, i) => (
                            <div key={i} className="bg-red-950/20 border border-red-800/30 rounded-xl p-4 space-y-2">
                                <p className="text-sm font-semibold text-red-300">{g.requirement}</p>
                                <p className="text-xs text-zinc-400 leading-relaxed">{g.description}</p>
                                {g.gap && <p className="text-xs text-red-300/80 leading-relaxed">{g.gap}</p>}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Gap Recommendations */}
            {regulatory_gap_recommendations?.length > 0 && (
                <div className="space-y-2">
                    <p className="text-xs font-bold uppercase tracking-widest text-zinc-500">Gap Recommendations</p>
                    <div className="space-y-3">
                        {regulatory_gap_recommendations.map((r, i) => (
                            <div key={i} className="bg-emerald-950/20 border border-emerald-800/30 rounded-xl p-4 space-y-2">
                                <p className="text-sm font-semibold text-emerald-300">{r.requirement}</p>
                                <p className="text-xs text-zinc-400 leading-relaxed">{r.description}</p>
                                {r.gap && <p className="text-xs text-emerald-300/80 leading-relaxed">{r.gap}</p>}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

function isFindingsSchema(data) {
    return 'findings' in data || 'regulatory_gaps' in data || 'regulatory_requirements' in data;
}

const MASTER_SCHEMA_KEYS = new Set([
    'executive_summary', 'risk_assessment', 'sentiment_outlook',
    'governance_compliance', 'points_of_agreement', 'points_of_contentions',
    'key_metrics', 'investment_considerations', 'final_recommendation', 'discussion_summary'
]);

function isMasterSchema(data) {
    const keys = Object.keys(data);
    return keys.some(k => MASTER_SCHEMA_KEYS.has(k));
}

// ─── Master Report Renderer ───────────────────────────────────────────────────

function MasterReportRenderer({ data }) {
    const {
        executive_summary,
        risk_assessment,
        sentiment_outlook,
        governance_compliance,
        points_of_agreement,
        points_of_contentions,
        key_metrics,
        investment_considerations,
        final_recommendation,
        discussion_summary,
    } = data;

    const recKey = (final_recommendation?.recommendation || '').toLowerCase().split(' ')[0];
    const RecIcon = recKey === 'outperform' ? TrendingUp : recKey === 'underperform' ? TrendingDown : Minus;

    return (
        <div className="space-y-6 text-sm">

            {/* ── Recommendation banner ── */}
            {final_recommendation && (
                <div className="flex items-center justify-between bg-zinc-950/70 border border-zinc-700 rounded-xl px-5 py-4">
                    <div className="flex items-center gap-3">
                        <RecIcon className="w-5 h-5 text-zinc-400" />
                        <div>
                            <p className="text-xs text-zinc-500 mb-0.5">Final Recommendation</p>
                            <Badge value={final_recommendation.recommendation} size="lg" />
                        </div>
                    </div>
                    <div className="text-right">
                        <p className="text-xs text-zinc-500 mb-0.5">Confidence</p>
                        <Badge value={final_recommendation.confidence_level} />
                    </div>
                </div>
            )}

            {/* ── Executive Summary ── */}
            {executive_summary && (
                <>
                    <Section title="Executive Summary">
                        <p className="text-zinc-300 leading-relaxed">{executive_summary}</p>
                    </Section>
                    <Divider />
                </>
            )}

            {/* ── Risk / Sentiment / Governance row ── */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

                {risk_assessment && (
                    <div className="bg-zinc-950/50 border border-zinc-800 rounded-xl p-4 space-y-3">
                        <div className="flex items-center justify-between">
                            <span className="text-xs font-bold uppercase tracking-widest text-zinc-500">Risk</span>
                            <Badge value={risk_assessment.risk_level} />
                        </div>
                        <p className="text-zinc-300 text-xs leading-relaxed">{risk_assessment.summary}</p>
                        {risk_assessment.primary_risks?.length > 0 && (
                            <ul className="space-y-1">
                                {risk_assessment.primary_risks.map((r, i) => (
                                    <li key={i} className="flex gap-2 text-xs text-zinc-400">
                                        <span className="text-red-500 mt-0.5">▸</span>{r}
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                )}

                {sentiment_outlook && (
                    <div className="bg-zinc-950/50 border border-zinc-800 rounded-xl p-4 space-y-3">
                        <div className="flex items-center justify-between">
                            <span className="text-xs font-bold uppercase tracking-widest text-zinc-500">Outlook</span>
                            <Badge value={sentiment_outlook.market_outlook} />
                        </div>
                        <p className="text-zinc-300 text-xs leading-relaxed">{sentiment_outlook.summary}</p>
                        <div className="flex items-center justify-between text-xs">
                            <span className="text-zinc-500">Mgmt Confidence</span>
                            <Badge value={sentiment_outlook.management_confidence} />
                        </div>
                    </div>
                )}

                {governance_compliance && (
                    <div className="bg-zinc-950/50 border border-zinc-800 rounded-xl p-4 space-y-3">
                        <div className="flex items-center justify-between">
                            <span className="text-xs font-bold uppercase tracking-widest text-zinc-500">Governance</span>
                            <Badge value={governance_compliance.governance_risk} />
                        </div>
                        <p className="text-zinc-300 text-xs leading-relaxed">{governance_compliance.summary}</p>
                        <div className="text-xs text-zinc-400">{governance_compliance.compliance_status}</div>
                        {governance_compliance.confidence_score != null && (
                            <ScoreBar value={governance_compliance.confidence_score} label="Confidence" />
                        )}
                    </div>
                )}
            </div>

            <Divider />

            {/* ── Key Metrics ── */}
            {key_metrics?.length > 0 && (
                <Section title="Key Metrics">
                    <div className="overflow-x-auto">
                        <table className="w-full text-xs">
                            <thead>
                                <tr className="border-b border-zinc-800">
                                    <th className="text-left py-2 pr-4 text-zinc-500 font-medium">Metric</th>
                                    <th className="text-left py-2 pr-4 text-zinc-500 font-medium">Finding</th>
                                    <th className="text-left py-2 text-zinc-500 font-medium">Implication</th>
                                </tr>
                            </thead>
                            <tbody>
                                {key_metrics.map((m, i) => (
                                    <tr key={i} className="border-b border-zinc-800/50">
                                        <td className="py-2 pr-4 text-zinc-300 font-medium whitespace-nowrap">{m.metric}</td>
                                        <td className="py-2 pr-4 text-zinc-200">{m.finding}</td>
                                        <td className="py-2 text-zinc-400">{m.implication}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </Section>
            )}

            <Divider />

            {/* ── Investment Considerations ── */}
            {investment_considerations && (
                <Section title="Investment Considerations">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {investment_considerations.strengths?.length > 0 && (
                            <div className="bg-emerald-950/30 border border-emerald-800/30 rounded-lg p-3">
                                <p className="text-xs font-semibold text-emerald-400 mb-2">Strengths</p>
                                <ul className="space-y-1">
                                    {investment_considerations.strengths.map((s, i) => (
                                        <li key={i} className="flex gap-2 text-xs text-zinc-300">
                                            <span className="text-emerald-500 mt-0.5">+</span>{s}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                        {investment_considerations.concerns?.length > 0 && (
                            <div className="bg-red-950/30 border border-red-800/30 rounded-lg p-3">
                                <p className="text-xs font-semibold text-red-400 mb-2">Concerns</p>
                                <ul className="space-y-1">
                                    {investment_considerations.concerns.map((c, i) => (
                                        <li key={i} className="flex gap-2 text-xs text-zinc-300">
                                            <span className="text-red-500 mt-0.5">−</span>{c}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </Section>
            )}

            <Divider />

            {/* ── Agreement / Contention ── */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {points_of_agreement?.length > 0 && (
                    <Section title="Points of Agreement">
                        <ul className="space-y-1.5">
                            {points_of_agreement.map((p, i) => (
                                <li key={i} className="flex gap-2 text-xs text-zinc-300">
                                    <span className="text-emerald-500 mt-0.5 shrink-0">✓</span>{p}
                                </li>
                            ))}
                        </ul>
                    </Section>
                )}
                {points_of_contentions?.length > 0 && (
                    <Section title="Points of Contention">
                        <div className="space-y-2">
                            {points_of_contentions.map((c, i) => (
                                <div key={i} className="bg-zinc-950/50 border border-zinc-800 rounded-lg p-3">
                                    <p className="text-zinc-200 text-xs font-medium mb-1">{c.issue}</p>
                                    <p className="text-zinc-400 text-xs">{c.resolution}</p>
                                </div>
                            ))}
                        </div>
                    </Section>
                )}
            </div>

            {/* ── Discussion Summary ── */}
            {discussion_summary && (
                <>
                    <Divider />
                    <Section title="Discussion Summary">
                        <p className="text-zinc-400 text-xs leading-relaxed italic">{discussion_summary}</p>
                    </Section>
                </>
            )}
        </div>
    );
}

// ─── FinalReport ──────────────────────────────────────────────────────────────

function FinalReport({ report, isLoading }) {
    const [copied, setCopied] = React.useState(false);

    const parsed = tryParseJson(report);

    const handleCopy = async () => {
        if (report) {
            await navigator.clipboard.writeText(report);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const handleDownload = () => {
        if (report) {
            const ext  = parsed ? 'json' : 'md';
            const type = parsed ? 'application/json' : 'text/markdown';
            const blob = new Blob([report], { type });
            const url  = URL.createObjectURL(blob);
            const a    = document.createElement('a');
            a.href = url;
            a.download = `earnings-analysis-report.${ext}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    };

    return (
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl overflow-hidden">
            <div className="px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center">
                        <FileText className="w-4 h-4 text-white" />
                    </div>
                    <div>
                        <h3 className="font-medium text-zinc-200">Final Analysis Report</h3>
                        <p className="text-xs text-zinc-500">Consolidated by Master Analyst</p>
                    </div>
                </div>

                {report && (
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleCopy}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-zinc-400
                         bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
                        >
                            {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                            {copied ? 'Copied!' : 'Copy'}
                        </button>
                        <button
                            onClick={handleDownload}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-zinc-400
                         bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
                        >
                            <Download className="w-3.5 h-3.5" />
                            Download
                        </button>
                    </div>
                )}
            </div>

            <div className="p-6 min-h-[400px] max-h-[800px] overflow-y-auto">
                {isLoading && (
                    <div className="flex flex-col items-center justify-center py-16">
                        <Loader2 className="w-10 h-10 text-indigo-400 animate-spin mb-4" />
                        <p className="text-zinc-400">Master Analyst is consolidating findings...</p>
                        <div className="mt-6 w-full max-w-md space-y-3">
                            <div className="h-4 bg-zinc-800 rounded shimmer" />
                            <div className="h-4 bg-zinc-800 rounded w-5/6 shimmer" />
                            <div className="h-4 bg-zinc-800 rounded w-4/5 shimmer" />
                        </div>
                    </div>
                )}

                {!isLoading && !report && (
                    <div className="flex flex-col items-center justify-center py-16 text-center">
                        <div className="w-16 h-16 rounded-full bg-zinc-800 flex items-center justify-center mb-4">
                            <FileText className="w-7 h-7 text-zinc-500" />
                        </div>
                        <p className="text-zinc-500">Waiting for analysis to complete...</p>
                    </div>
                )}

                {!isLoading && report && (
                    parsed && isMasterSchema(parsed)  ? <MasterReportRenderer data={parsed} />
                    : parsed && isFindingsSchema(parsed) ? <FindingsReportRenderer data={parsed} />
                    : parsed                             ? <GenericJsonRenderer data={parsed} />
                    : <article className="prose-custom"><ReactMarkdown>{report}</ReactMarkdown></article>
                )}
            </div>
        </div>
    );
}

export default FinalReport;
