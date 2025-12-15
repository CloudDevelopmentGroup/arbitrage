import React, { useState } from 'react';
import { CurrencyDollarIcon, MagnifyingGlassIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import axios from 'axios';
import LoadingSpinner from './LoadingSpinner';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://1biv76cy0j.execute-api.us-east-1.amazonaws.com';

function SingleItemChecker({ onBackToUpload }) {
    const [formData, setFormData] = useState({
        item_number: '',
        title: '',
        msrp: '',
        quantity: '1',
        notes: ''
    });
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysisResult, setAnalysisResult] = useState(null);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        // Validation
        if (!formData.title.trim()) {
            toast.error('Please enter an item title');
            return;
        }
        
        const msrp = parseFloat(formData.msrp);
        if (!msrp || msrp <= 0) {
            toast.error('Please enter a valid MSRP greater than 0');
            return;
        }

        setIsAnalyzing(true);
        setAnalysisResult(null);

        try {
            const response = await axios.post(`${API_BASE_URL}/prod/check-item`, {
                item_number: formData.item_number,
                title: formData.title,
                msrp: formData.msrp,
                quantity: parseInt(formData.quantity) || 1,
                notes: formData.notes
            }, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            setAnalysisResult(response.data);
            toast.success('Item analyzed successfully!');
        } catch (error) {
            console.error('Analysis error:', error);
            if (error.response && error.response.data && error.response.data.error) {
                toast.error(error.response.data.error);
            } else {
                toast.error('Failed to analyze item. Please try again.');
            }
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleReset = () => {
        setFormData({
            item_number: '',
            title: '',
            msrp: '',
            quantity: '1',
            notes: ''
        });
        setAnalysisResult(null);
    };

    const getDemandColor = (demand) => {
        switch (demand) {
            case 'High':
                return 'text-green-600 bg-green-50';
            case 'Medium':
                return 'text-yellow-600 bg-yellow-50';
            case 'Low':
                return 'text-red-600 bg-red-50';
            default:
                return 'text-gray-600 bg-gray-50';
        }
    };

    const getProfitColor = (profit) => {
        if (profit >= 50) return 'text-green-600';
        if (profit >= 20) return 'text-yellow-600';
        return 'text-red-600';
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900">Check Single Item</h2>
                        <p className="text-sm text-gray-500 mt-1">
                            Quickly analyze individual items without uploading a manifest
                        </p>
                    </div>
                    {onBackToUpload && (
                        <button
                            onClick={onBackToUpload}
                            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                        >
                            ← Back to CSV Upload
                        </button>
                    )}
                </div>
            </div>

            {!analysisResult ? (
                /* Input Form */
                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="bg-white rounded-lg shadow-sm p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Item Details</h3>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Item Number */}
                            <div>
                                <label htmlFor="item_number" className="block text-sm font-medium text-gray-700 mb-2">
                                    Item Number (Optional)
                                </label>
                                <input
                                    type="text"
                                    id="item_number"
                                    name="item_number"
                                    value={formData.item_number}
                                    onChange={handleInputChange}
                                    placeholder="e.g., SKU, Part #, Model #"
                                    className="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                />
                            </div>

                            {/* MSRP */}
                            <div>
                                <label htmlFor="msrp" className="block text-sm font-medium text-gray-700 mb-2">
                                    MSRP <span className="text-red-500">*</span>
                                </label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <span className="text-gray-500 sm:text-sm">$</span>
                                    </div>
                                    <input
                                        type="number"
                                        id="msrp"
                                        name="msrp"
                                        value={formData.msrp}
                                        onChange={handleInputChange}
                                        placeholder="0.00"
                                        step="0.01"
                                        min="0"
                                        required
                                        className="w-full pl-7 pr-4 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Title */}
                        <div className="mt-4">
                            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                                Item Title / Description <span className="text-red-500">*</span>
                            </label>
                            <input
                                type="text"
                                id="title"
                                name="title"
                                value={formData.title}
                                onChange={handleInputChange}
                                placeholder="Enter the full item name or description"
                                required
                                className="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>

                        {/* Quantity */}
                        <div className="mt-4">
                            <label htmlFor="quantity" className="block text-sm font-medium text-gray-700 mb-2">
                                Quantity
                            </label>
                            <input
                                type="number"
                                id="quantity"
                                name="quantity"
                                value={formData.quantity}
                                onChange={handleInputChange}
                                placeholder="1"
                                min="1"
                                className="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>

                        {/* Notes */}
                        <div className="mt-4">
                            <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-2">
                                Notes (Optional)
                            </label>
                            <textarea
                                id="notes"
                                name="notes"
                                value={formData.notes}
                                onChange={handleInputChange}
                                placeholder="Any additional notes about the item (condition, location, etc.)"
                                rows="3"
                                className="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>
                    </div>

                    {/* Submit Button */}
                    <div className="bg-white rounded-lg shadow-sm p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600">
                                    AI will analyze this item's resale potential
                                </p>
                            </div>
                            <div className="flex space-x-3">
                                <button
                                    type="button"
                                    onClick={handleReset}
                                    className="px-6 py-3 border border-gray-300 rounded-md text-base font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                >
                                    Reset
                                </button>
                                <button
                                    type="submit"
                                    disabled={isAnalyzing}
                                    className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isAnalyzing ? (
                                        <>
                                            <LoadingSpinner />
                                            <span className="ml-2">Analyzing...</span>
                                        </>
                                    ) : (
                                        <>
                                            <MagnifyingGlassIcon className="h-5 w-5 mr-2" />
                                            Analyze Item
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>
                </form>
            ) : (
                /* Analysis Results */
                <div className="space-y-6">
                    {/* Item Info */}
                    <div className="bg-white rounded-lg shadow-sm p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Item Information</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <p className="text-sm text-gray-500">Item Number</p>
                                <p className="text-base font-medium text-gray-900">{analysisResult.item.item_number}</p>
                            </div>
                            <div>
                                <p className="text-sm text-gray-500">MSRP</p>
                                <p className="text-base font-medium text-gray-900">${analysisResult.item.msrp.toFixed(2)}</p>
                            </div>
                            <div className="md:col-span-2">
                                <p className="text-sm text-gray-500">Title</p>
                                <p className="text-base font-medium text-gray-900">{analysisResult.item.title}</p>
                            </div>
                            {analysisResult.item.notes && (
                                <div className="md:col-span-2">
                                    <p className="text-sm text-gray-500">Notes</p>
                                    <p className="text-base text-gray-700">{analysisResult.item.notes}</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Analysis Results */}
                    <div className="bg-white rounded-lg shadow-sm p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Analysis Results</h3>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                            <div className="bg-blue-50 rounded-lg p-4">
                                <p className="text-sm text-gray-600 mb-1">Estimated Sale Price</p>
                                <p className="text-2xl font-bold text-blue-600">
                                    ${analysisResult.analysis.estimatedSalePrice.toFixed(2)}
                                </p>
                            </div>
                            <div className="bg-green-50 rounded-lg p-4">
                                <p className="text-sm text-gray-600 mb-1">Suggested Purchase Price</p>
                                <p className="text-2xl font-bold text-green-600">
                                    ${analysisResult.analysis.purchasePrice.toFixed(2)}
                                </p>
                            </div>
                            <div className={`rounded-lg p-4 ${analysisResult.analysis.profitPerItem >= 20 ? 'bg-green-50' : 'bg-yellow-50'}`}>
                                <p className="text-sm text-gray-600 mb-1">Profit Per Item</p>
                                <p className={`text-2xl font-bold ${getProfitColor(analysisResult.analysis.profitPerItem)}`}>
                                    ${analysisResult.analysis.profitPerItem.toFixed(2)}
                                </p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <p className="text-sm text-gray-500 mb-2">Demand Level</p>
                                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getDemandColor(analysisResult.analysis.demand)}`}>
                                    {analysisResult.analysis.demand}
                                </span>
                            </div>
                            <div>
                                <p className="text-sm text-gray-500 mb-2">Estimated Sales Time</p>
                                <p className="text-base font-medium text-gray-900">{analysisResult.analysis.salesTime}</p>
                            </div>
                        </div>

                        <div className="mt-4">
                            <p className="text-sm text-gray-500 mb-2">AI Reasoning</p>
                            <p className="text-base text-gray-700 bg-gray-50 p-3 rounded-md">
                                {analysisResult.analysis.reasoning}
                            </p>
                        </div>
                    </div>

                    {/* Summary (with quantity) */}
                    {analysisResult.summary.quantity > 1 && (
                        <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg shadow-lg p-6 text-white">
                            <h3 className="text-lg font-semibold mb-4">
                                Total Summary ({analysisResult.summary.quantity} items)
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                                <div>
                                    <p className="text-blue-100 text-sm mb-1">Total Investment</p>
                                    <p className="text-2xl font-bold">${analysisResult.summary.totalInvestment.toFixed(2)}</p>
                                </div>
                                <div>
                                    <p className="text-blue-100 text-sm mb-1">Total Revenue</p>
                                    <p className="text-2xl font-bold">${analysisResult.summary.totalRevenue.toFixed(2)}</p>
                                </div>
                                <div>
                                    <p className="text-blue-100 text-sm mb-1">Total Profit</p>
                                    <p className="text-2xl font-bold">${analysisResult.summary.totalProfit.toFixed(2)}</p>
                                </div>
                                <div>
                                    <p className="text-blue-100 text-sm mb-1">ROI</p>
                                    <p className="text-2xl font-bold">{analysisResult.summary.roi.toFixed(1)}%</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Action Buttons */}
                    <div className="bg-white rounded-lg shadow-sm p-6">
                        <div className="flex items-center justify-center space-x-4">
                            <button
                                onClick={handleReset}
                                className="inline-flex items-center px-6 py-3 border border-gray-300 rounded-md text-base font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                                <ArrowPathIcon className="h-5 w-5 mr-2" />
                                Check Another Item
                            </button>
                            {onBackToUpload && (
                                <button
                                    onClick={onBackToUpload}
                                    className="inline-flex items-center px-6 py-3 border border-transparent rounded-md text-base font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                >
                                    <CurrencyDollarIcon className="h-5 w-5 mr-2" />
                                    Analyze Full Manifest
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default SingleItemChecker;

