import React, { useState, useCallback, useRef } from 'react';
import { Upload, FileText, Sparkles, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

function UploadZone({ onUpload, isDisabled, parserState }) {
    const [textContent, setTextContent] = useState('');
    const [dragActive, setDragActive] = useState(false);
    const [uploadedFile, setUploadedFile] = useState(null);
    const fileInputRef = useRef(null);

    const handleDrag = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0];
            if (file.type === 'application/pdf') {
                setUploadedFile(file);
                setTextContent('');
            }
        }
    }, []);

    const handleFileSelect = useCallback((e) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            if (file.type === 'application/pdf') {
                setUploadedFile(file);
                setTextContent('');
            }
        }
    }, []);

    const handleSubmit = useCallback(() => {
        if (uploadedFile) {
            onUpload(null, true, uploadedFile);
        } else if (textContent.trim()) {
            onUpload(textContent, false, null);
        }
    }, [uploadedFile, textContent, onUpload]);

    const clearFile = useCallback(() => {
        setUploadedFile(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    }, []);

    const getParserStatusIcon = () => {
        switch (parserState) {
            case 'thinking':
                return <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />;
            case 'complete':
                return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
            case 'error':
                return <AlertCircle className="w-5 h-5 text-red-400" />;
            default:
                return null;
        }
    };

    return (
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center">
                        <FileText className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h2 className="text-lg font-semibold text-white">Upload Earnings Report</h2>
                        <p className="text-sm text-zinc-500">Paste text or upload a PDF document</p>
                    </div>
                </div>
                {getParserStatusIcon()}
            </div>

            <div className="grid md:grid-cols-2 gap-6">
                {/* Text Input Area */}
                <div className="space-y-3">
                    <label className="block text-sm font-medium text-zinc-400">
                        Paste Report Text
                    </label>
                    <textarea
                        value={textContent}
                        onChange={(e) => {
                            setTextContent(e.target.value);
                            setUploadedFile(null);
                        }}
                        disabled={isDisabled}
                        placeholder="Paste your earnings report content here..."
                        className="w-full h-48 px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-xl
                       text-zinc-300 placeholder-zinc-600 resize-none
                       focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-transparent
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-all duration-200"
                    />
                </div>

                {/* File Upload Area */}
                <div className="space-y-3">
                    <label className="block text-sm font-medium text-zinc-400">
                        Upload PDF
                    </label>
                    <div
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                        onClick={() => !isDisabled && fileInputRef.current?.click()}
                        className={`
              h-48 border-2 border-dashed rounded-xl flex flex-col items-center justify-center
              cursor-pointer transition-all duration-200
              ${dragActive
                                ? 'border-indigo-500 bg-indigo-500/10'
                                : 'border-zinc-700 bg-zinc-900/50 hover:border-zinc-600'
                            }
              ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}
            `}
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".pdf"
                            onChange={handleFileSelect}
                            className="hidden"
                            disabled={isDisabled}
                        />

                        {uploadedFile ? (
                            <div className="text-center">
                                <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-emerald-600/20 
                                flex items-center justify-center">
                                    <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                                </div>
                                <p className="text-sm font-medium text-zinc-300 mb-1">
                                    {uploadedFile.name}
                                </p>
                                <p className="text-xs text-zinc-500">
                                    {(uploadedFile.size / 1024).toFixed(1)} KB
                                </p>
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        clearFile();
                                    }}
                                    className="mt-2 text-xs text-red-400 hover:text-red-300"
                                >
                                    Remove
                                </button>
                            </div>
                        ) : (
                            <>
                                <Upload className={`w-8 h-8 mb-3 ${dragActive ? 'text-indigo-400' : 'text-zinc-500'}`} />
                                <p className="text-sm text-zinc-400 text-center">
                                    Drag & drop your PDF here
                                </p>
                                <p className="text-xs text-zinc-600 mt-1">
                                    or click to browse
                                </p>
                            </>
                        )}
                    </div>
                </div>
            </div>

            {/* Submit Button */}
            <div className="mt-6 flex justify-end">
                <button
                    onClick={handleSubmit}
                    disabled={isDisabled || (!textContent.trim() && !uploadedFile)}
                    className="flex items-center gap-2 px-6 py-3 
                     bg-indigo-600 hover:bg-indigo-500
                     text-white font-medium rounded-xl
                     transition-colors duration-200
                     disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <Sparkles className="w-4 h-4" />
                    Start Analysis
                </button>
            </div>
        </div>
    );
}

export default UploadZone;
