import React from 'react';
import { CheckCircle2, Loader2 } from 'lucide-react';

function PhaseIndicator({ phases, currentPhase, isProcessing }) {
    return (
        <div className="mb-8">
            <div className="flex items-center justify-between max-w-2xl mx-auto">
                {phases.map((phase, index) => {
                    const Icon = phase.icon;
                    const isActive = currentPhase === phase.id;
                    const isComplete = currentPhase > phase.id;
                    const isPending = currentPhase < phase.id;

                    return (
                        <React.Fragment key={phase.id}>
                            {/* Phase Node */}
                            <div className="flex flex-col items-center">
                                <div
                                    className={`
                    w-12 h-12 rounded-full flex items-center justify-center
                    transition-all duration-300 relative
                    ${isComplete ? 'bg-indigo-600 text-white' : ''}
                    ${isActive ? 'bg-indigo-600/20 text-indigo-400 ring-2 ring-indigo-600' : ''}
                    ${isPending ? 'bg-zinc-800 text-zinc-500' : ''}
                  `}
                                >
                                    {isComplete ? (
                                        <CheckCircle2 className="w-5 h-5" />
                                    ) : isActive && isProcessing ? (
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                    ) : (
                                        <Icon className="w-5 h-5" />
                                    )}
                                </div>

                                <span className={`
                  mt-2 text-xs font-medium transition-colors duration-300
                  ${isComplete ? 'text-indigo-400' : ''}
                  ${isActive ? 'text-indigo-400' : ''}
                  ${isPending ? 'text-zinc-500' : ''}
                `}>
                                    {phase.label}
                                </span>
                            </div>

                            {/* Connector Line */}
                            {index < phases.length - 1 && (
                                <div className="flex-1 h-0.5 mx-4 relative">
                                    <div className="absolute inset-0 bg-zinc-800 rounded-full" />
                                    <div
                                        className="absolute inset-y-0 left-0 bg-indigo-600 rounded-full transition-all duration-500"
                                        style={{
                                            width: currentPhase > phase.id
                                                ? '100%'
                                                : currentPhase === phase.id
                                                    ? '50%'
                                                    : '0%'
                                        }}
                                    />
                                </div>
                            )}
                        </React.Fragment>
                    );
                })}
            </div>
        </div>
    );
}

export default PhaseIndicator;
