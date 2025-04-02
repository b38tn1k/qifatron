// =============================
// app.js
// =============================

const HIGHLIGHT = 0.1;

var hasPMIColor, hasFailureModeColor, hasOpenStroke, baseColor, hasFailureStroke, baseStroke, packageWithPMI, packageWithoutPMI, progressInProgressColor, progressSucessColor, progressFailureColor;
const software_corner_radius = 10;
const file_format_corner_radius = 0;

function setup() {
    const container = document.getElementById("canvasContainer");
    const w = container.clientWidth;
    const h = container.clientHeight;
    let canvas = createCanvas(w, h);
    canvas.parent("canvasContainer");
    textAlign(CENTER, CENTER);
    computeLayout();
    strokeJoin(BEVEL);

    hasPMIColor = color(200, 255, 255);
    hasFailureModeColor = color(255, 200, 200);
    hasOpenStroke = color(0, 155, 0)
    baseColor = color(255, 255, 255);
    baseStroke = color(0, 0, 0);
    hasFailureStroke = color(255, 0, 0);
    packageWithPMI = color(200, 255, 200);
    packageWithoutPMI = color(255, 200, 255);
    progressInProgressColor = color(255, 255, 200);
    progressSucessColor = color(200, 255, 200);
    progressFailureColor = color(255, 200, 200);
    setupButtons();
}

function draw() {
    // Draw zone boundaries and labels.
    clear();
    zones.forEach(zone => {
        strokeWeight(1);
        stroke(0);
        fill(240);
        rect(2, zone.yStart, width - 4, zone.yEnd - zone.yStart);
        noStroke();
        fill(0);
        textAlign(LEFT, CENTER);
        text(zone.name, 10, zone.yStart + 15);
    });


    // Draw connections between nodes.
    connections.forEach(conn => {
        const n1 = nodes[conn.from];
        const n2 = nodes[conn.to];
        if (n1 && n2) {
            stroke(50);
            strokeWeight(conn.type === "strong" ? 3 : 1);
            line(n1.x + BOX_WIDTH / 2, n1.y + BOX_HEIGHT / 2, n2.x + BOX_WIDTH / 2, n2.y + BOX_HEIGHT / 2);
        }
    });

    // Draw nodes.
    Object.values(nodes).forEach(node => {
        let cornerRadius = node.type === "Software" ? software_corner_radius : file_format_corner_radius;
        let fillColor = node.PMI === true ? hasPMIColor : baseColor;
        fillColor = node.failure_mode === true ? hasFailureModeColor : fillColor;

        let strokeColor = node.proprietary === true ? baseStroke : hasOpenStroke;
        strokeColor = node.failure_mode === true ? hasFailureStroke : strokeColor;
        if (node.type === "File Package") {
            fillColor = packageWithoutPMI;
            if (node.PMI === true) {
                fillColor = packageWithPMI;
            }
            
        }
        if (currentStatus) {
            if (currentStatus.success_journey && currentStatus.success_journey.includes(node.id)) {
                stroke(0);
                fill(progressSucessColor);
                strokeWeight(1);
                let w = BOX_WIDTH + BOX_WIDTH * HIGHLIGHT;
                let h = BOX_HEIGHT + BOX_WIDTH * HIGHLIGHT;
                rect(node.x - (w - BOX_WIDTH) / 2, node.y - (h - BOX_HEIGHT) / 2, w, h);
            }

            if (currentStatus.failure_journey && currentStatus.failure_journey.includes(node.id)) {
                stroke(0);
                fill(progressFailureColor);
                strokeWeight(1);
                let w = BOX_WIDTH + BOX_WIDTH * HIGHLIGHT;
                let h = BOX_HEIGHT + BOX_WIDTH * HIGHLIGHT;
                rect(node.x - (w - BOX_WIDTH) / 2, node.y - (h - BOX_HEIGHT) / 2, w, h);
            }

            if (currentStatus.in_progress && currentStatus.in_progress.includes(node.id)) {
                stroke(0);
                fill(progressInProgressColor);
                strokeWeight(1);
                let w = BOX_WIDTH + BOX_WIDTH * HIGHLIGHT;
                let h = BOX_HEIGHT + BOX_WIDTH * HIGHLIGHT;
                rect(node.x - (w - BOX_WIDTH) / 2, node.y - (h - BOX_HEIGHT) / 2, w, h);
            }

        }

        stroke(strokeColor);
        fill(fillColor);
        strokeWeight(1);

        rect(node.x, node.y, BOX_WIDTH, BOX_HEIGHT, cornerRadius);
        noStroke();
        fill(0);
        textAlign(CENTER, CENTER);
        let ts = textSize();
        if (node.type === "File Package") {
            textSize(ts * 0.8);
            let py = node.y + BOX_HEIGHT / 3;
            let inc = BOX_HEIGHT / (node.components.length + 1);
            for (let comp of node.components) {
                text("+ " + comp, node.x + BOX_WIDTH / 2, py);
                py += inc;

            }
            textSize(ts);
        } else if (node.version) {
            text(node.title, node.x + BOX_WIDTH / 2, node.y + BOX_HEIGHT / 3);
            textSize(ts * 0.8);
            text(node.version, node.x + BOX_WIDTH / 2, node.y + 3 * BOX_HEIGHT / 4);
            textSize(ts);

        } else {
            text(node.title, node.x + BOX_WIDTH / 2, node.y + BOX_HEIGHT / 2);
        }

    });
}

function windowResized() {
    clear();
    const container = document.getElementById("canvasContainer");
    const w = container.clientWidth;
    const h = container.clientHeight;
    resizeCanvas(w, h);
    computeLayout();
}



// =============================
// Legend Sketch (p5 instance mode)
// =============================
let legendSketch = (p) => {
    p.setup = function () {
        const container = document.getElementById("legendMount");
        const w = container.clientWidth;
        const h = container.clientHeight || 400;
        let canvas = p.createCanvas(w, h);
        canvas.parent("legendMount");
        p.noLoop(); // only need to draw once
    };

    p.draw = function () {
        p.clear();
        drawLegendBlockOn(p);
    };
};

function drawLegendBlockOn(p) {
    // make the canvas have enoguht width to fit the container
    const swatchSize = 20;
    const lineSpacing = 25;
    const padding = 10;
    const numRows = 9;
    const legendWidth = 230;
    const legendHeight = numRows * lineSpacing + padding;

    let x = 10;
    let y = 10;

    p.push();

    p.fill(255);
    p.stroke(0);
    p.strokeWeight(2);
    p.rect(x, y, legendWidth, legendHeight);

    let currentX = x + padding;
    let currentY = y + padding;
    p.fill(baseStroke);
    p.noStroke();

    // (1) File Format
    p.fill(baseColor);
    p.stroke(baseStroke);
    p.strokeWeight(2);
    p.rect(currentX, currentY, swatchSize, swatchSize, file_format_corner_radius);
    p.noStroke();
    p.fill(0);
    p.text("File Format (sharp corners)", currentX + swatchSize + 8, currentY + swatchSize / 2);

    currentY += lineSpacing;
    p.fill(baseColor);
    p.stroke(baseStroke);
    p.strokeWeight(2);
    p.rect(currentX, currentY, swatchSize, swatchSize, software_corner_radius);
    p.noStroke();
    p.fill(0);
    p.text("Software (rounded corners)", currentX + swatchSize + 8, currentY + swatchSize / 2);

    currentY += lineSpacing;
    p.fill(baseColor);
    p.stroke(hasOpenStroke);
    p.strokeWeight(2);
    p.rect(currentX, currentY, swatchSize, swatchSize);
    p.noStroke();
    p.fill(0);
    p.text("Open Protocol", currentX + swatchSize + 8, currentY + swatchSize / 2);

    currentY += lineSpacing;
    p.fill(baseColor);
    p.stroke(baseStroke);
    p.strokeWeight(2);
    p.rect(currentX, currentY, swatchSize, swatchSize);
    p.noStroke();
    p.fill(0);
    p.text("Proprietary Protocol", currentX + swatchSize + 8, currentY + swatchSize / 2);

    currentY += lineSpacing;
    p.fill(hasFailureModeColor);
    p.stroke(hasFailureStroke);
    p.strokeWeight(2);
    p.rect(currentX, currentY, swatchSize, swatchSize);
    p.noStroke();
    p.fill(0);
    p.text("Has Failure Mode", currentX + swatchSize + 8, currentY + swatchSize / 2);

    currentY += lineSpacing * 1.5;

    p.fill(packageWithoutPMI);
    p.stroke(baseStroke);
    p.strokeWeight(2);
    p.rect(currentX, currentY, swatchSize, swatchSize, file_format_corner_radius);
    p.noStroke();
    p.fill(0);
    p.text("File Package", currentX + swatchSize + 8, currentY + swatchSize / 2);

    currentY += lineSpacing;
    p.fill(packageWithPMI);
    p.stroke(baseStroke);
    p.strokeWeight(2);
    p.rect(currentX, currentY, swatchSize, swatchSize, file_format_corner_radius);
    p.noStroke();
    p.fill(0);
    p.text("File Package w/ PMI", currentX + swatchSize + 8, currentY + swatchSize / 2);

    currentY += lineSpacing * 1.5;
    p.fill(hasPMIColor);
    p.stroke(baseStroke);
    p.strokeWeight(2);
    p.rect(currentX, currentY, swatchSize, swatchSize);
    p.noStroke();
    p.fill(0);
    p.text("Has PMI", currentX + swatchSize + 8, currentY + swatchSize / 2);

    

    p.pop();
}

new p5(legendSketch);