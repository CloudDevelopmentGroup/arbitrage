import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
    ArrowUpTrayIcon as UploadIcon,
    DocumentIcon,
    ChartBarIcon,
    CurrencyDollarIcon,
    ClockIcon,
    MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import toast, { Toaster } from 'react-hot-toast';
import axios from 'axios';
import AnalysisResults from './components/AnalysisResults';
import LoadingSpinner from './components/LoadingSpinner';
import UploadHistory from './components/UploadHistory';
import SingleItemChecker from './components/SingleItemChecker';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://1biv76cy0j.execute-api.us-east-1.amazonaws.com';

function App() {
    const [uploadedFile, setUploadedFile] = useState(null);
    const [csvText, setCsvText] = useState('');
    const [analysisResults, setAnalysisResults] = useState(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [uploadMethod, setUploadMethod] = useState('file'); // 'file' or 'text'
    const [processingStatus, setProcessingStatus] = useState(null); // {processed: 0, total: 0}
    const [uploadId, setUploadId] = useState(null);
    const [uploadName, setUploadName] = useState('');
    const [uploadHistory, setUploadHistory] = useState([]);
    const [showHistory, setShowHistory] = useState(false);
    const [mode, setMode] = useState('manifest'); // 'manifest' or 'single-item'

    // Fetch upload history on component mount
    React.useEffect(() => {
        fetchUploadHistory();
    }, []);

    const fetchUploadHistory = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/prod/history`);
            setUploadHistory(response.data.uploads || []);
        } catch (error) {
            console.error('Error fetching history:', error);
        }
    };

    const handleSelectUpload = async (uploadId) => {
        try {
            setIsAnalyzing(true);
            const response = await axios.get(`${API_BASE_URL}/prod/status/${uploadId}`);
            setAnalysisResults(response.data);
            setShowHistory(false);
            toast.success('Analysis loaded!');
        } catch (error) {
            console.error('Error loading upload:', error);
            toast.error('Failed to load analysis');
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleDeleteUpload = async (uploadId) => {
        try {
            await axios.delete(`${API_BASE_URL}/prod/upload/${uploadId}`);
            toast.success('Upload deleted successfully!');

            // If the deleted upload is currently being viewed/processed, clear it
            if (analysisResults && analysisResults.upload_id === uploadId) {
                setAnalysisResults(null);
                setIsAnalyzing(false);
                setProcessingStatus(null);
                setShowHistory(true);  // Show history instead
            }

            // Refresh history
            await fetchUploadHistory();
        } catch (error) {
            console.error('Error deleting upload:', error);
            toast.error('Failed to delete upload');
        }
    };

    const onDrop = useCallback((acceptedFiles) => {
        const file = acceptedFiles[0];
        if (file && file.type === 'text/csv') {
            setUploadedFile(file);
            toast.success('CSV file uploaded successfully!');
        } else {
            toast.error('Please upload a valid CSV file');
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'text/csv': ['.csv']
        },
        multiple: false
    });

    const pollStatus = async (uploadId) => {
        try {
            const response = await axios.get(`${API_BASE_URL}/prod/status/${uploadId}`);
            const data = response.data;

            setProcessingStatus({
                processed: data.processed_items || 0,
                total: data.total_items || 0
            });

            // Show partial results while processing
            if (data.status === 'processing' && data.summary) {
                setAnalysisResults({
                    ...data,
                    items: [], // No items yet, just summary
                    summary: {
                        ...data.summary,
                        totalItems: data.total_items,
                        processedItems: data.processed_items,
                        partial: true
                    }
                });
            }

            if (data.status === 'completed') {
                // Processing complete, show full results
                setAnalysisResults(data);
                setIsAnalyzing(false);
                setProcessingStatus(null);
                toast.success('Analysis completed successfully!');
                return true; // Stop polling
            } else if (data.status === 'failed') {
                setIsAnalyzing(false);
                setProcessingStatus(null);
                toast.error(data.error_message || 'Processing failed');
                return true; // Stop polling
            }

            return false; // Continue polling
        } catch (error) {
            console.error('Status check error:', error);

            // If upload was deleted (404), stop polling and clear UI
            if (error.response && error.response.status === 404) {
                setIsAnalyzing(false);
                setProcessingStatus(null);
                setAnalysisResults(null);
                setShowHistory(true);
                toast.error('Upload was deleted');
                return true; // Stop polling
            }

            return false; // Continue polling
        }
    };

    const handleAnalysis = async () => {
        let fileContent = '';
        let filename = '';

        if (uploadMethod === 'file') {
            if (!uploadedFile) {
                toast.error('Please upload a CSV file first');
                return;
            }
            fileContent = await readFileAsText(uploadedFile);
            filename = uploadedFile.name;
        } else {
            if (!csvText.trim()) {
                toast.error('Please paste CSV data first');
                return;
            }
            fileContent = csvText;
            filename = 'pasted-data.csv';
        }

        setIsAnalyzing(true);
        setUploadProgress(0);
        setProcessingStatus(null);

        try {
            // Upload file and get upload_id
            const response = await axios.post(`${API_BASE_URL}/prod/upload`, {
                file: fileContent,
                filename: filename,
                upload_name: uploadName.trim() || null
            }, {
                headers: {
                    'Content-Type': 'application/json',
                },
                onUploadProgress: (progressEvent) => {
                    const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                    setUploadProgress(progress);
                },
            });

            if (response.status === 202) {
                // Async processing started
                const { upload_id, total_items } = response.data;
                setUploadId(upload_id);
                setProcessingStatus({ processed: 0, total: total_items });
                toast.success(`Processing ${total_items} items...`);

                // Start polling for status
                const pollInterval = setInterval(async () => {
                    const isDone = await pollStatus(upload_id);
                    if (isDone) {
                        clearInterval(pollInterval);
                    }
                }, 2000); // Poll every 2 seconds

                // Cleanup on unmount
                return () => clearInterval(pollInterval);
            } else {
                // Old sync response (fallback)
                setAnalysisResults(response.data);
                setIsAnalyzing(false);
                toast.success('Analysis completed successfully!');
            }
        } catch (error) {
            console.error('Analysis error:', error);
            toast.error('Failed to analyze CSV. Please try again.');
            setIsAnalyzing(false);
            setUploadProgress(0);
            setProcessingStatus(null);
        }
    };

    const readFileAsText = (file) => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e);
            reader.readAsText(file);
        });
    };

    const handleReset = () => {
        setUploadedFile(null);
        setCsvText('');
        setAnalysisResults(null);
        setIsAnalyzing(false);
        setUploadProgress(0);
        setUploadName('');
        fetchUploadHistory(); // Refresh history after completing analysis
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <Toaster position="top-right" />

            {/* Header */}
            <header className="bg-white shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center py-6">
                        <div className="flex items-center">
                            <ChartBarIcon className="h-8 w-8 text-blue-600 mr-3" />
                            <h1 className="text-2xl font-bold text-gray-900">Arbitrage Analyzer</h1>
                        </div>
                        <div className="flex items-center space-x-4">
                            {mode === 'manifest' && (
                                <button
                                    onClick={() => setMode('single-item')}
                                    className="inline-flex items-center px-4 py-2 border border-blue-600 rounded-md shadow-sm text-sm font-medium text-blue-600 bg-white hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                >
                                    <MagnifyingGlassIcon className="h-5 w-5 mr-2" />
                                    Check Single Item
                                </button>
                            )}
                            <button
                                onClick={() => {
                                    setShowHistory(!showHistory);
                                    if (!showHistory) fetchUploadHistory();
                                }}
                                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                                <ClockIcon className="h-5 w-5 mr-2 text-gray-500" />
                                {showHistory ? 'Hide History' : 'View History'}
                            </button>
                            <div className="text-sm text-gray-500">
                                AI-Powered Retail Arbitrage Analysis
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {showHistory ? (
                    <div className="space-y-6">
                        <UploadHistory
                            uploads={uploadHistory}
                            onSelectUpload={handleSelectUpload}
                            onDeleteUpload={handleDeleteUpload}
                        />
                        <div className="text-center">
                            <button
                                onClick={() => setShowHistory(false)}
                                className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                            >
                                ← Back to Upload
                            </button>
                        </div>
                    </div>
                ) : mode === 'single-item' ? (
                    <SingleItemChecker 
                        onBackToUpload={() => setMode('manifest')}
                    />
                ) : !analysisResults ? (
                    <div className="space-y-8">
                        {/* Upload Name Input */}
                        <div className="bg-white rounded-lg shadow-sm p-6">
                            <h2 className="text-lg font-semibold text-gray-900 mb-4">
                                Name Your Analysis
                            </h2>
                            <div>
                                <label htmlFor="upload-name" className="block text-sm font-medium text-gray-700 mb-2">
                                    Give this upload a memorable name (optional)
                                </label>
                                <input
                                    type="text"
                                    id="upload-name"
                                    value={uploadName}
                                    onChange={(e) => setUploadName(e.target.value)}
                                    placeholder="e.g., Staples Manifest Jan 2025, Wayfair Pallet #123"
                                    className="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    maxLength={100}
                                />
                                <p className="mt-2 text-xs text-gray-500">
                                    A timestamp will be automatically appended to ensure uniqueness
                                </p>
                            </div>
                        </div>

                        {/* Upload Method Selection */}
                        <div className="bg-white rounded-lg shadow-sm p-6">
                            <h2 className="text-lg font-semibold text-gray-900 mb-4">
                                Upload Manifest CSV
                            </h2>

                            <div className="mb-6">
                                <div className="flex space-x-4">
                                    <button
                                        onClick={() => setUploadMethod('file')}
                                        className={`px-4 py-2 rounded-md text-sm font-medium ${uploadMethod === 'file'
                                            ? 'bg-blue-600 text-white'
                                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                            }`}
                                    >
                                        Upload File
                                    </button>
                                    <button
                                        onClick={() => setUploadMethod('text')}
                                        className={`px-4 py-2 rounded-md text-sm font-medium ${uploadMethod === 'text'
                                            ? 'bg-blue-600 text-white'
                                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                            }`}
                                    >
                                        Paste CSV Data
                                    </button>
                                </div>
                            </div>

                            {uploadMethod === 'file' ? (
                                <div>
                                    <div
                                        {...getRootProps()}
                                        className={`upload-zone ${isDragActive ? 'dragover' : ''}`}
                                    >
                                        <input {...getInputProps()} />
                                        <UploadIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                                        {isDragActive ? (
                                            <p className="text-lg text-blue-600">Drop the CSV file here...</p>
                                        ) : (
                                            <div>
                                                <p className="text-lg text-gray-600 mb-2">
                                                    Drag & drop your manifest CSV here, or click to select
                                                </p>
                                                <p className="text-sm text-gray-500">
                                                    Supports any manifest CSV format (Grainger, generic products, parts, etc.)
                                                </p>
                                            </div>
                                        )}
                                    </div>

                                    {uploadedFile && (
                                        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                                            <div className="flex items-center">
                                                <DocumentIcon className="h-5 w-5 text-green-600 mr-2" />
                                                <span className="text-sm font-medium text-green-800">
                                                    {uploadedFile.name}
                                                </span>
                                                <span className="text-sm text-green-600 ml-2">
                                                    ({(uploadedFile.size / 1024).toFixed(1)} KB)
                                                </span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div>
                                    <label htmlFor="csv-text" className="block text-sm font-medium text-gray-700 mb-2">
                                        Paste your CSV data below:
                                    </label>
                                    <textarea
                                        id="csv-text"
                                        value={csvText}
                                        onChange={(e) => setCsvText(e.target.value)}
                                        placeholder="Paste your CSV data here..."
                                        className="w-full h-64 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                                    />
                                    <p className="mt-2 text-sm text-gray-500">
                                        Supports any manifest CSV format (Grainger, generic products, parts, etc.)
                                    </p>
                                </div>
                            )}
                        </div>

                        {/* Analysis Button */}
                        <div className="bg-white rounded-lg shadow-sm p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-lg font-medium text-gray-900">Ready to Analyze</h3>
                                    <p className="text-sm text-gray-500">
                                        {uploadMethod === 'file'
                                            ? (uploadedFile ? `File: ${uploadedFile.name}` : 'No file uploaded')
                                            : (csvText.trim() ? 'CSV data ready' : 'No CSV data pasted')
                                        }
                                    </p>
                                </div>
                                <button
                                    onClick={handleAnalysis}
                                    disabled={isAnalyzing || (uploadMethod === 'file' ? !uploadedFile : !csvText.trim())}
                                    className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isAnalyzing ? (
                                        <>
                                            <LoadingSpinner />
                                            <span className="ml-2">Analyzing...</span>
                                        </>
                                    ) : (
                                        <>
                                            <CurrencyDollarIcon className="h-5 w-5 mr-2" />
                                            Analyze Manifest
                                        </>
                                    )}
                                </button>
                            </div>

                            {isAnalyzing && (
                                <div className="mt-4">
                                    <div className="bg-gray-200 rounded-full h-2">
                                        <div
                                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                            style={{
                                                width: processingStatus
                                                    ? `${Math.round((processingStatus.processed / processingStatus.total) * 100)}%`
                                                    : `${uploadProgress}%`
                                            }}
                                        ></div>
                                    </div>
                                    <p className="text-sm text-gray-600 mt-2">
                                        {processingStatus ? (
                                            <>
                                                Processing items: {processingStatus.processed} / {processingStatus.total}
                                                {' '}({Math.round((processingStatus.processed / processingStatus.total) * 100)}%)
                                            </>
                                        ) : (
                                            `Uploading... ${uploadProgress}%`
                                        )}
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    <AnalysisResults
                        results={analysisResults}
                        onReset={handleReset}
                        fileName={uploadMethod === 'file' ? uploadedFile?.name : 'pasted-data.csv'}
                    />
                )}
            </main>
        </div>
    );
}

export default App;