#!/usr/bin/env python3
"""
Test script for the item checker Lambda function
Can be run locally before deployment
"""

import json
import sys
import os

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lambda'))

from item_checker import lambda_handler

def test_single_item():
    """Test analyzing a single item"""
    print("Testing single item analysis...")
    print("-" * 50)
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'item_number': 'TEST123',
            'title': 'Milwaukee M18 Cordless Power Drill Kit',
            'msrp': 199.99,
            'quantity': 1,
            'notes': 'New in box, sealed'
        })
    }
    
    context = {}
    
    try:
        response = lambda_handler(event, context)
        
        print(f"Status Code: {response['statusCode']}")
        print("\nResponse Body:")
        body = json.loads(response['body'])
        print(json.dumps(body, indent=2))
        
        if response['statusCode'] == 200:
            print("\n✓ Test passed!")
            return True
        else:
            print("\n✗ Test failed!")
            return False
            
    except Exception as e:
        print(f"\n✗ Test error: {str(e)}")
        return False

def test_bulk_quantity():
    """Test analyzing multiple quantities"""
    print("\n\nTesting bulk quantity analysis...")
    print("-" * 50)
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'item_number': 'BULK456',
            'title': 'Industrial Air Compressor 60 Gallon',
            'msrp': 899.99,
            'quantity': 10,
            'notes': 'Liquidation pallet'
        })
    }
    
    context = {}
    
    try:
        response = lambda_handler(event, context)
        
        print(f"Status Code: {response['statusCode']}")
        print("\nResponse Body:")
        body = json.loads(response['body'])
        print(json.dumps(body, indent=2))
        
        if response['statusCode'] == 200:
            analysis = body
            print("\n--- Summary ---")
            print(f"Quantity: {analysis['summary']['quantity']}")
            print(f"Total Investment: ${analysis['summary']['totalInvestment']}")
            print(f"Total Revenue: ${analysis['summary']['totalRevenue']}")
            print(f"Total Profit: ${analysis['summary']['totalProfit']}")
            print(f"ROI: {analysis['summary']['roi']}%")
            print("\n✓ Test passed!")
            return True
        else:
            print("\n✗ Test failed!")
            return False
            
    except Exception as e:
        print(f"\n✗ Test error: {str(e)}")
        return False

def test_invalid_input():
    """Test with invalid input"""
    print("\n\nTesting invalid input handling...")
    print("-" * 50)
    
    test_cases = [
        {
            'name': 'Missing title',
            'body': {'msrp': 100}
        },
        {
            'name': 'Invalid MSRP',
            'body': {'title': 'Test Item', 'msrp': -50}
        },
        {
            'name': 'Zero MSRP',
            'body': {'title': 'Test Item', 'msrp': 0}
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        event = {
            'httpMethod': 'POST',
            'body': json.dumps(test_case['body'])
        }
        
        try:
            response = lambda_handler(event, {})
            if response['statusCode'] == 400:
                print("✓ Correctly returned 400 error")
            else:
                print(f"✗ Expected 400, got {response['statusCode']}")
                all_passed = False
        except Exception as e:
            print(f"✗ Unexpected error: {str(e)}")
            all_passed = False
    
    return all_passed

def test_cors_preflight():
    """Test CORS preflight request"""
    print("\n\nTesting CORS preflight...")
    print("-" * 50)
    
    event = {
        'httpMethod': 'OPTIONS'
    }
    
    context = {}
    
    try:
        response = lambda_handler(event, context)
        
        if response['statusCode'] == 200:
            print("✓ CORS preflight test passed!")
            return True
        else:
            print(f"✗ Expected 200, got {response['statusCode']}")
            return False
            
    except Exception as e:
        print(f"\n✗ Test error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Item Checker Lambda Function Tests")
    print("=" * 50)
    
    # Note: These tests use mock analysis since OpenAI API key may not be set
    print("\nNote: Tests use mock analysis (OpenAI API key not required)")
    
    results = []
    
    results.append(('Single Item', test_single_item()))
    results.append(('Bulk Quantity', test_bulk_quantity()))
    results.append(('Invalid Input', test_invalid_input()))
    results.append(('CORS Preflight', test_cors_preflight()))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())

