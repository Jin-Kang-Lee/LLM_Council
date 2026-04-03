import React, { useState, useCallback } from 'react';
import {
    BarChart3,
    Brain,
    FileText,
    MessageSquare,
    CheckCircle2,
} from 'lucide-react';
import UploadZone from './components/UploadZone';
import AgentCards from './components/AgentCards';
import DiscussionLog from './components/DiscussionLog';
import FinalReport from './components/FinalReport';
import Header from './components/Header';
import PhaseIndicator from './components/PhaseIndicator';

const API_BASE = 'http://localhost:8000';

function App() {
    const [currentPhase, setCurrentPhase] = useState(0);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState(null);

    const [parsedContent, setParsedContent] = useState(null);
    const [riskAnalysis, setRiskAnalysis] = useState(null);
    const [businessOpsAnalysis, setBusinessOpsAnalysis] = useState(null);
    const [governanceAnalysis, setGovernanceAnalysis] = useState(null);
    const [referenceContexts, setReferenceContexts] = useState({
        risk: null,
        business_ops: null,
        governance: null,
    });
    const [referenceQueries, setReferenceQueries] = useState({
        risk: null,
        business_ops: null,
        governance: null,
    });
    const [discussionMessages, setDiscussionMessages] = useState([]);
    const [finalReport, setFinalReport] = useState(null);

    const [agentStates, setAgentStates] = useState({
        parser: 'idle',
        risk: 'idle',
        business_ops: 'idle',
        governance: 'idle',
        master: 'idle'
    });

    const resetAnalysis = useCallback(() => {
        setCurrentPhase(0);
        setIsProcessing(false);
        setError(null);
        setParsedContent(null);
        setRiskAnalysis(null);
        setBusinessOpsAnalysis(null);
        setGovernanceAnalysis(null);
        setReferenceContexts({
            risk: null,
            business_ops: null,
            governance: null,
        });
        setReferenceQueries({
            risk: null,
            business_ops: null,
            governance: null,
        });
        setDiscussionMessages([]);
        setFinalReport(null);
        setAgentStates({
            parser: 'idle',
            risk: 'idle',
            business_ops: 'idle',
            governance: 'idle',
            master: 'idle'
        });
    }, []);

    const handleUpload = useCallback(async (content, isPdf = false, file = null) => {
        setError(null);
        setIsProcessing(true);
        setCurrentPhase(1);
        setAgentStates(prev => ({ ...prev, parser: 'thinking' }));

        try {
            let response;

            if (isPdf && file) {
                const formData = new FormData();
                formData.append('file', file);
                response = await fetch(`${API_BASE}/analyze/pdf`, {
                    method: 'POST',
                    body: formData
                });
            } else {
                response = await fetch(`${API_BASE}/analyze/text`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content })
                });
            }

            if (!response.ok) {
                throw new Error('Failed to initialize analysis');
            }

            const data = await response.json();
            setParsedContent(data.parsed);
            setAgentStates(prev => ({ ...prev, parser: 'complete' }));

            const eventSource = new EventSource(`${API_BASE}/analyze/stream/${data.session_id}`);

            eventSource.addEventListener('phase', (event) => {
                const phaseData = JSON.parse(event.data);
                setCurrentPhase(phaseData.phase);

                if (phaseData.phase === 4 && phaseData.status === 'started') {
                    setAgentStates(prev => ({ ...prev, master: 'thinking' }));
                }
            });

            eventSource.addEventListener('agent', (event) => {
                const agentData = JSON.parse(event.data);

                if (agentData.agent === 'risk') {
                    setAgentStates(prev => ({
                        ...prev,
                        risk: agentData.status === 'complete' ? 'complete' : 'thinking'
                    }));
                    if (agentData.content) {
                        setRiskAnalysis(agentData.content);
                    }
                    if (agentData.reference_context) {
                        setReferenceContexts(prev => ({ ...prev, risk: agentData.reference_context }));
                    }
                    if (agentData.reference_query) {
                        setReferenceQueries(prev => ({ ...prev, risk: agentData.reference_query }));
                    }
                } else if (agentData.agent === 'business_ops') {
                    setAgentStates(prev => ({
                        ...prev,
                        business_ops: agentData.status === 'complete' ? 'complete' : 'thinking'
                    }));
                    if (agentData.content) {
                        setBusinessOpsAnalysis(agentData.content);
                    }
                    if (agentData.reference_context) {
                        setReferenceContexts(prev => ({ ...prev, business_ops: agentData.reference_context }));
                    }
                    if (agentData.reference_query) {
                        setReferenceQueries(prev => ({ ...prev, business_ops: agentData.reference_query }));
                    }
                } else if (agentData.agent === 'governance') {
                    setAgentStates(prev => ({
                        ...prev,
                        governance: agentData.status === 'complete' ? 'complete' : 'thinking'
                    }));
                    if (agentData.content) {
                        setGovernanceAnalysis(agentData.content);
                    }
                    if (agentData.reference_context) {
                        setReferenceContexts(prev => ({ ...prev, governance: agentData.reference_context }));
                    }
                    if (agentData.reference_query) {
                        setReferenceQueries(prev => ({ ...prev, governance: agentData.reference_query }));
                    }
                }
            });

            eventSource.addEventListener('message', (event) => {
                const messageData = JSON.parse(event.data);
                setDiscussionMessages(prev => [...prev, {
                    agent: messageData.agent,
                    agentName: messageData.agentName,
                    content: messageData.content,
                    round: messageData.round
                }]);
            });

            eventSource.addEventListener('report', (event) => {
                const reportData = JSON.parse(event.data);
                setFinalReport(reportData.content);
                setAgentStates(prev => ({ ...prev, master: 'complete' }));
            });

            eventSource.addEventListener('complete', () => {
                setIsProcessing(false);
                eventSource.close();
            });

            eventSource.addEventListener('error', (event) => {
                console.error('SSE Error:', event);
                setError('Connection lost. Please try again.');
                setIsProcessing(false);
                eventSource.close();
            });

        } catch (err) {
            setError(err.message);
            setIsProcessing(false);
            setAgentStates(prev => ({ ...prev, parser: 'error' }));
        }
    }, []);

    const phases = [
        { id: 1, label: 'Parse', icon: FileText },
        { id: 2, label: 'Analyze', icon: Brain },
        { id: 3, label: 'Discuss', icon: MessageSquare },
        { id: 4, label: 'Report', icon: BarChart3 }
    ];

    return (
        <div className="min-h-screen bg-[#0a0a0b]">
            <Header onReset={resetAnalysis} isProcessing={isProcessing} />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <PhaseIndicator
                    phases={phases}
                    currentPhase={currentPhase}
                    isProcessing={isProcessing}
                />

                {error && (
                    <div className="mb-6 p-4 bg-red-900/20 border border-red-800/50 rounded-lg text-red-400">
                        <p className="flex items-center gap-2">
                            <span className="font-medium">Error:</span> {error}
                        </p>
                    </div>
                )}

                <section className="mb-8">
                    <UploadZone
                        onUpload={handleUpload}
                        isDisabled={isProcessing}
                        parserState={agentStates.parser}
                    />
                </section>

                {currentPhase >= 2 && (
                    <section className="mb-8">
                        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                            <Brain className="w-5 h-5 text-indigo-400" />
                            Individual Analysis
                        </h2>
                        <AgentCards
                            riskAnalysis={riskAnalysis}
                            businessOpsAnalysis={businessOpsAnalysis}
                            governanceAnalysis={governanceAnalysis}
                            riskState={agentStates.risk}
                            businessOpsState={agentStates.business_ops}
                            governanceState={agentStates.governance}
                            parserState={agentStates.parser}
                            parsedContent={parsedContent}
                            riskReferenceContext={referenceContexts.risk}
                            businessOpsReferenceContext={referenceContexts.business_ops}
                            governanceReferenceContext={referenceContexts.governance}
                            riskReferenceQuery={referenceQueries.risk}
                            businessOpsReferenceQuery={referenceQueries.business_ops}
                            governanceReferenceQuery={referenceQueries.governance}
                        />
                    </section>
                )}

                {currentPhase >= 3 && (
                    <section className="mb-8">
                        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                            <MessageSquare className="w-5 h-5 text-indigo-400" />
                            Agent War Room
                        </h2>
                        <DiscussionLog
                            messages={discussionMessages}
                            isActive={currentPhase === 3 && isProcessing}
                            referenceContexts={referenceContexts}
                            referenceQueries={referenceQueries}
                        />
                    </section>
                )}

                {currentPhase >= 4 && (
                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                            <BarChart3 className="w-5 h-5 text-emerald-400" />
                            Consolidated Report
                            {agentStates.master === 'complete' && (
                                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                            )}
                        </h2>
                        <FinalReport
                            report={finalReport}
                            isLoading={agentStates.master === 'thinking'}
                        />
                    </section>
                )}
            </main>

            <footer className="border-t border-zinc-800/50 mt-12 py-6">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <p className="text-center text-zinc-600 text-sm">
                        Multi-Agent Earnings Analyzer • Powered by Local LLMs via Ollama
                    </p>
                </div>
            </footer>
        </div>
    );
}

export default App;
