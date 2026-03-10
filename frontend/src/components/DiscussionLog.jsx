import React, { useEffect, useRef } from 'react';
import { ShieldAlert, Heart, MessageCircle, Gavel } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

function MessageBubble({ message }) {
    const getAgentStyles = () => {
        switch (message.agent) {
            case 'risk':
                return { color: 'bg-red-600', text: 'text-red-400', border: 'border-red-900/30', icon: ShieldAlert };
            case 'sentiment':
                return { color: 'bg-emerald-600', text: 'text-emerald-400', border: 'border-emerald-900/30', icon: Heart };
            case 'governance':
                return { color: 'bg-purple-600', text: 'text-purple-400', border: 'border-purple-900/30', icon: Gavel };
            default:
                return { color: 'bg-zinc-600', text: 'text-zinc-400', border: 'border-zinc-900/30', icon: MessageCircle };
        }
    };

    const styles = getAgentStyles();
    const isPrimary = message.agent === 'risk'; // Left-aligned

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
                </div>
                <div className="prose-custom text-sm">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
            </div>
        </div>
    );
}

function DiscussionLog({ messages, isActive }) {
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
                    <MessageBubble key={index} message={message} />
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
