/**
 * Calculates the right span coordinate (x) for each scanline (y)
 * of the top semicircle using Bresenham's Midpoint Algorithm.
 * Assumes center at (0,0).
 *
 * @param {number} radius The radius of the circle.
 * @returns {number[]} An array where the index is the y-coordinate (0 to radius)
 * and the value is the corresponding right span x-coordinate.
 * 
 * Author: Gemini 2.5 Pro
 */
function calculateSemicircleSpans(radius) {
    if (radius < 0) return []; // Handle invalid radius
    if (radius === 0) return [0]; // Circle of radius 0 is a single point

    const spans = new Array(radius + 1); // Array to store x-span for each y
    let x = 0;
    let y = radius;
    // Initial decision parameter (derived from evaluating circle eqn at midpoint (1, R-0.5))
    // Using the common integer form p = 1 - R
    let p = 1 - radius;

    // Store the initial topmost point's span
    // For y = radius, the x coordinate is 0.
    spans[y] = x; // spans[radius] = 0

    // Iterate while generating points in the second octant (from top moving rightwards)
    // Loop condition x < y ensures we only calculate one octant.
    while (x < y) {
        x++; // Always move right

        if (p <= 0) {
            // Midpoint is inside or on the circle, choose E pixel
            // p_new = p_old + 2x_new + 1
            p = p + 2 * x + 1;
        } else {
            // Midpoint is outside the circle, choose SE pixel
            y--; // Move down
            // p_new = p_old + 2x_new + 1 - 2y_new
            p = p + 2 * x + 1 - 2 * y;
        }

        // Store the calculated span `x` for the current scanline `y`.
        // This covers the second octant part of the semicircle.
        // Check bounds for safety although y should decrease correctly.
        if (y >= 0 && y <= radius) {
             spans[y] = x;
        }

        // Use symmetry to store the span for the first octant part.
        // The point (y, x) is symmetric to (x, y) across the y=x line.
        // This means for scanline `x`, the span is `y`.
        // Check bounds for safety.
        if (x >= 0 && x <= radius) {
             spans[x] = y;
        }
    }

    // Ensure all entries are filled (especially near the x=y transition)
    // Sometimes due to integer steps, one value might be missed if the loop
    // condition stops exactly right. Forward/backward fill can help,
    // but usually the symmetry assignment handles it. Let's double check:
    // If the loop finished, spans[y] = x and spans[x] = y were the last stores.
    // Example: R=5. Loop ends when x=4, y=4. Stores spans[4]=4.
    // We need spans[0] to spans[5].
    // R=5:
    // Init: x=0, y=5, p=-4. spans=[,,,,0]
    // x=1, p=-4+3=-1 <=0. spans=[,,,,0] -> Store spans[5]=1, spans[1]=5? No, x=1,y=5 is current point. Store spans[y]=x -> spans[5]=1. Store spans[x]=y -> spans[1]=5. Array: [,5,,,,1]
    // x=2, p=-1+5=4 > 0. y=4. p=4+5-8=1. spans=[,5,,,?,1] -> Store spans[y]=x -> spans[4]=2. Store spans[x]=y -> spans[2]=4. Array: [,5,4,,2,1]
    // x=3, p=1+7=8 > 0. y=3. p=8+7-6=9. spans=[,5,4,?,2,1] -> Store spans[y]=x -> spans[3]=3. Store spans[x]=y -> spans[3]=3. Array: [,5,4,3,2,1]
    // x=4, y=3. x < y is false. Loop terminates.
    // We seem to be missing spans[0]. The lowest y reached was 3.
    // The last point on the circle is (R, 0). So spans[0] should be R.
    // Let's add this explicitly.
    spans[0] = radius;

    // The algorithm might leave gaps if y decreases by more than 1 in a step
    // (which Bresenham doesn't) or if the symmetry doesn't perfectly fill.
    // Let's fill any remaining undefined downward from the top.
    // Scanlines just below a calculated one should have at least the same span.
     for (let currentY = radius - 1; currentY >= 0; currentY--) {
        if (spans[currentY] === undefined) {
           // If undefined, take span from the line above.
           // This handles cases where y might jump, though unlikely here.
           // More importantly, ensures values like spans[0] are set if loop ends early.
           // Or better: Use the previous span calculated for a higher y.
           // The x span should generally increase or stay the same as y decreases.
           spans[currentY] = spans[currentY + 1];
        }
        // Also ensure span does not decrease as we go down
        if (spans[currentY] < spans[currentY + 1]) {
            spans[currentY] = spans[currentY + 1];
        }
     }
     // Ensure the span at y=0 is the radius
     spans[0] = radius;


    return spans;
}

/**
 * Displays the spans array and a text visualization of the semicircle.
 *
 * @param {number} radius The radius used.
 * @param {number[]} spans The calculated spans array.
 */
function displaySemicircle(radius, spans) {
    const spansOutput = document.getElementById('spansOutput');
    const semicircleOutput = document.getElementById('semicircleOutput');

    // Display Spans Array
    let spansText = `Radius: ${radius}\n`;
    spansText += " y | x (right span)\n";
    spansText += "---|---------------\n";
    // Print from y=radius down to y=0
    for (let y = radius; y >= 0; y--) {
        spansText += `${String(y).padStart(2, ' ')} | ${spans[y]}\n`;
    }
    spansOutput.textContent = spansText;

    // Display Semicircle Visualization
    let semicircleText = "";
    const screenWidth = 2 * radius + 1;
    const centerX = radius; // Center column index (0-based)

    // Draw from y = radius down to y = 0
    for (let y = radius; y >= 0; y--) {
        const rightSpan = spans[y]; // x coordinate relative to center
        const leftPixelPos = centerX - rightSpan;
        const rightPixelPos = centerX + rightSpan;

        let line = "";
        for (let screenX = 0; screenX < screenWidth; screenX++) {
            if (screenX === leftPixelPos || screenX === rightPixelPos) {
                line += "*";
            } else {
                line += " ";
            }
        }
        semicircleText += line + "\n";
    }
    semicircleOutput.textContent = semicircleText;
}

/**
 * Main function to get input, run algorithm, and display results.
 */
function runAlgorithm() {
    const radiusInput = document.getElementById('radiusInput');
    const radius = parseInt(radiusInput.value, 10);

    if (isNaN(radius) || radius < 0) {
        alert("Please enter a valid non-negative integer radius.");
        return;
    }

    const spans = calculateSemicircleSpans(radius);
    displaySemicircle(radius, spans);
}

// Initial run on load
window.onload = () => {
   runAlgorithm();
};