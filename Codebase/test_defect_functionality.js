// Test script to verify defect clear button functionality
// This would be run in a browser console to test the implementation

console.log('Testing defect clear button functionality...');

// Test 1: Check if updateDefectHasValueClass function exists
if (typeof updateDefectHasValueClass === 'function') {
    console.log('✅ updateDefectHasValueClass function is defined');
} else {
    console.log('❌ updateDefectHasValueClass function is NOT defined');
}

// Test 2: Check if initializeDefectHasValueClasses function exists  
if (typeof initializeDefectHasValueClasses === 'function') {
    console.log('✅ initializeDefectHasValueClasses function is defined');
} else {
    console.log('❌ initializeDefectHasValueClasses function is NOT defined');
}

// Test 3: Simulate defect input testing
console.log('\nSimulating defect input testing...');

// Create a mock HTML structure for testing
const mockHTML = `
    <div class="defect-input-group">
        <input type="text" class="defect-input-side" data-side="left" data-meter="1">
        <button type="button" class="defect-clear-btn">×</button>
    </div>
`;

// If running in browser, test with actual DOM elements
if (typeof document !== 'undefined') {
    // Test with existing defect inputs
    const defectInputs = document.querySelectorAll('.defect-input-side, .defect-input-center');
    console.log(`Found ${defectInputs.length} defect inputs on page`);
    
    const clearButtons = document.querySelectorAll('.defect-clear-btn');
    console.log(`Found ${clearButtons.length} clear buttons on page`);
    
    // Test updateDefectHasValueClass functionality
    if (defectInputs.length > 0) {
        const firstInput = defectInputs[0];
        const originalValue = firstInput.value;
        
        // Test with empty value
        firstInput.value = '';
        updateDefectHasValueClass(firstInput);
        const clearButton = firstInput.closest('.defect-input-group')?.querySelector('.defect-clear-btn');
        
        if (clearButton && !clearButton.classList.contains('has-value')) {
            console.log('✅ Empty input correctly removes has-value class');
        } else {
            console.log('❌ Empty input does NOT remove has-value class');
        }
        
        // Test with non-empty value
        firstInput.value = 'Test defect';
        updateDefectHasValueClass(firstInput);
        
        if (clearButton && clearButton.classList.contains('has-value')) {
            console.log('✅ Non-empty input correctly adds has-value class');
        } else {
            console.log('❌ Non-empty input does NOT add has-value class');
        }
        
        // Restore original value
        firstInput.value = originalValue;
        updateDefectHasValueClass(firstInput);
    }
}

console.log('\nTest completed. Check the console for results.');