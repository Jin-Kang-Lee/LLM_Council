import React from 'react';
import { FileText, Loader2, Download, Copy, CheckCircle2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

function FinalReport({ report, isLoading }) {
    const [copied, setCopied] = React.useState(false);

    const handleCopy = async () => {
        if (report) {
            await navigator.clipboard.writeText(report);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const handleDownload = () => {
        if (report) {
            const blob = new Blob([report], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'earnings-analysis-report.md';
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
                    <article className="prose-custom">
                        <ReactMarkdown>{report}</ReactMarkdown>
                    </article>
                )}
            </div>
        </div>
    );
}

export default FinalReport;
