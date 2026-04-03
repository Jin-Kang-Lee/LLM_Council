import React, { useEffect, useRef, useState } from 'react';
import { ShieldAlert, Heart, MessageCircle, Gavel, TrendingUp } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

function MessageBubble({ message, referenceContexts, referenceQueries }) {
    const getAgentStyles = () => {
        switch (message.agent) {
            case 'risk':
                return { color: 'bg-red-600', text: 'text-red-400', border: 'border-red-900/30', icon: ShieldAlert };
            case 'business_ops':
                return { color: 'bg-yellow-600', text: 'text-yellow-400', border: 'border-yellow-900/30', icon: TrendingUp };
            case 'governance':
                return { color: 'bg-purple-600', text: 'text-purple-400', border: 'border-purple-900/30', icon: Gavel };
            default:
                return { color: 'bg-zinc-600', text: 'text-zinc-400', border: 'border-zinc-900/30', icon: MessageCircle };
        }
    };

    const styles = getAgentStyles();
    const isPrimary = message.agent === 'risk'; // Left-aligned
    const [showReference, setShowReference] = useState(false);
    const referenceContext = referenceContexts?.[message.agent];
    const referenceQuery = referenceQueries?.[message.agent];

    return (
        <div className={`flex gap-3 ${isPrimary ? '' : 'flex-row-reverse'}`}>
            <div className={`
        flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center
        ${styles.color}
      `}>
                <styles.icon className="w-5 h-5 text-white" />
            </div>

            <div className={`
        flex-1 max-w-[80%] rounded-2xl px-4 py-3 bg-zinc-800/50 border ${styles.border}
        ${isPrimary ? 'rounded-tl-md' : 'rounded-tr-md'}
      `}>
                <div className="flex items-center gap-2 mb-2">
                    <span className={`text-sm font-medium ${styles.text}`}>
                        {message.agentName}
                    </span>
                    <span className="text-xs text-zinc-600">Round {message.round}</span>
                    {referenceContext && (
                        <button
                            type="button"
                            onClick={() => setShowReference(prev => !prev)}
                            className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500/30 transition-colors"
                        >
                            {showReference ? 'Hide RAG' : 'Show RAG'}
                        </button>
                    )}
                </div>
                <div className="prose-custom text-sm">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
                {referenceContext && showReference && (
                    <div className="mt-3 text-xs text-zinc-300 bg-zinc-950/60 border border-zinc-800 rounded p-3 max-h-48 overflow-y-auto whitespace-pre-wrap">
                        {referenceQuery && (
                            <div className="text-zinc-500 mb-2">
                                <span className="font-semibold">Query:</span> {referenceQuery}
                            </div>
                        )}
                        <pre className="whitespace-pre-wrap font-sans">{referenceContext}</pre>
                    </div>
                )}
            </div>
        </div>
    );
}

function DiscussionLog({ messages, isActive, referenceContexts, referenceQueries }) {
    const scrollRef = useRef(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    return (
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl overflow-hidden">
            <div className="px-4 py-3 border-b border-zinc-800 flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
                    <MessageCircle className="w-4 h-4 text-white" />
                </div>
                <div className="flex-1">
                    <h3 className="font-medium text-zinc-200">Council Discussion</h3>
                </div>
                {isActive && (
                    <div className="flex items-center gap-2 px-3 py-1 bg-indigo-600/20 rounded-full">
                        <div className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
                        <span className="text-xs text-indigo-400">Live</span>
                    </div>
                )}
            </div>

            <div ref={scrollRef} className="p-4 space-y-4 max-h-[500px] overflow-y-auto">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                        <div className="w-16 h-16 rounded-full bg-zinc-800 flex items-center justify-center mb-4">
                            <MessageCircle className="w-7 h-7 text-zinc-500" />
                        </div>
                        <p className="text-zinc-500">Waiting for agents to start discussion...</p>
                    </div>
                )}
                {messages.map((message, index) => (
                    <MessageBubble
                        key={index}
                        message={message}
                        referenceContexts={referenceContexts}
                        referenceQueries={referenceQueries}
                    />
                ))}
            </div>

            {messages.length > 0 && (
                <div className="px-4 py-2 border-t border-zinc-800 bg-zinc-900/50">
                    <p className="text-xs text-zinc-500 text-center">
                        {messages.length} messages • {Math.ceil(messages.length / 2)} rounds
                    </p>
                </div>
            )}
        </div>
    );
}

export default DiscussionLog;
