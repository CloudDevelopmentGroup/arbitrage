import React from 'react';
import { ClockIcon, CheckCircleIcon, ArrowPathIcon, XCircleIcon, TrashIcon } from '@heroicons/react/24/outline';

function UploadHistory({ uploads, onSelectUpload, onDeleteUpload }) {
    const getStatusIcon = (status) => {
        switch (status) {
            case 'completed':
                return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
            case 'processing':
                return <ArrowPathIcon className="h-5 w-5 text-blue-500 animate-spin" />;
            case 'failed':
                return <XCircleIcon className="h-5 w-5 text-red-500" />;
            default:
                return <ClockIcon className="h-5 w-5 text-gray-500" />;
        }
    };

    const getStatusText = (status) => {
        switch (status) {
            case 'completed':
                return 'Completed';
            case 'processing':
                return 'Processing';
            case 'failed':
                return 'Failed';
            default:
                return 'Pending';
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed':
                return 'bg-green-50 text-green-700 border-green-200';
            case 'processing':
                return 'bg-blue-50 text-blue-700 border-blue-200';
            case 'failed':
                return 'bg-red-50 text-red-700 border-red-200';
            default:
                return 'bg-gray-50 text-gray-700 border-gray-200';
        }
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'Unknown';
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            timeZone: 'America/New_York',
            timeZoneName: 'short'
        });
    };

    if (!uploads || uploads.length === 0) {
        return (
            <div className="bg-white rounded-lg shadow-sm p-8 text-center">
                <ClockIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Upload History</h3>
                <p className="text-sm text-gray-500">
                    Your analysis history will appear here after your first upload.
                </p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow-sm">
            <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Upload History</h2>
                <p className="text-sm text-gray-500 mt-1">
                    View and access your previous analyses
                </p>
            </div>

            <div className="divide-y divide-gray-200">
                {uploads.map((upload) => (
                    <div
                        key={upload.upload_id}
                        onClick={() => upload.status === 'completed' && onSelectUpload(upload.upload_id)}
                        className={`px-6 py-4 ${upload.status === 'completed'
                            ? 'cursor-pointer hover:bg-gray-50 transition-colors'
                            : 'cursor-default'
                            }`}
                    >
                        <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center space-x-3">
                                    {getStatusIcon(upload.status)}
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-gray-900 truncate">
                                            {upload.upload_name || upload.filename}
                                        </p>
                                        <p className="text-xs text-gray-500 mt-1">
                                            {formatDate(upload.created_at)}
                                        </p>
                                    </div>
                                </div>

                                <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                                    <span>
                                        {upload.total_items} {upload.total_items === 1 ? 'item' : 'items'}
                                    </span>
                                    {upload.status === 'processing' && (
                                        <span className="text-blue-600">
                                            {upload.processed_items} / {upload.total_items} processed
                                        </span>
                                    )}
                                </div>
                            </div>

                            <div className="ml-4 flex items-center space-x-2">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(upload.status)}`}>
                                    {getStatusText(upload.status)}
                                </span>
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        if (window.confirm(`Delete "${upload.upload_name || upload.filename}"?`)) {
                                            onDeleteUpload(upload.upload_id);
                                        }
                                    }}
                                    className="p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors"
                                    title="Delete upload"
                                >
                                    <TrashIcon className="h-5 w-5" />
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default UploadHistory;

