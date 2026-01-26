import React from 'react';
import { BarChart3, RefreshCw } from 'lucide-react';

function Header({ onReset, isProcessing }) {
    return (
        <header className="border-b border-zinc-800/50 bg-zinc-950 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">
                    {/* Logo & Title */}
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center">
                            <BarChart3 className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h1 className="text-lg font-semibold text-white">
                                Earnings Analyzer
                            </h1>
                            <p className="text-xs text-zinc-500">
                                Multi-Agent AI System
                            </p>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-4">
                        <button
                            onClick={onReset}
                            disabled={isProcessing}
                            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-zinc-300 
                         bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors
                         disabled:opacity-50 disabled:cursor-not-allowed
                         hover:text-white"
                        >
                            <RefreshCw className={`w-4 h-4 ${isProcessing ? 'animate-spin' : ''}`} />
                            <span className="hidden sm:inline">New Analysis</span>
                        </button>
                    </div>
                </div>
            </div>
        </header>
    );
}

export default Header;
