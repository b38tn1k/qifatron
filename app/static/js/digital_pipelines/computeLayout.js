// =============================
// treeLayout.js
// =============================

const BOX_WIDTH_RATIO = 0.1;
const BOX_HEIGHT_RATIO = 0.05;
const ZONE_PADDING_RATIO = 0.02;
const ZONE_START_RATIO = 0.01;
const MARGIN_RATIO = 0.05;
const LEVEL_SPACING_RATIO = 0.08;
const ZONE_TOP_MARGIN_RATIO = 0.04;
const NODE_TOP_MARGIN_RATIO = 0.02;
const NODE_BOTTOM_MARGIN_RATIO = 0.02;

var BOX_WIDTH = 150;
var BOX_HEIGHT = 30;
var ZONE_PADDING = 20;
var ZONE_START = 2;
var MARGIN = 100;
var LEVEL_SPACING = 80;
var ZONE_TOP_MARGIN = 30;
var NODE_TOP_MARGIN = 20;
var NODE_BOTTOM_MARGIN = 20;


function computeDrawingGeometries() {
    BOX_WIDTH = width * BOX_WIDTH_RATIO;
    BOX_HEIGHT = height * BOX_HEIGHT_RATIO;
    ZONE_PADDING = height * ZONE_PADDING_RATIO;
    ZONE_START = height * ZONE_START_RATIO;
    MARGIN = width * MARGIN_RATIO;
    LEVEL_SPACING = height * LEVEL_SPACING_RATIO;
    ZONE_TOP_MARGIN = height * ZONE_TOP_MARGIN_RATIO;
    NODE_TOP_MARGIN = height * NODE_TOP_MARGIN_RATIO;
    NODE_BOTTOM_MARGIN = height * NODE_BOTTOM_MARGIN_RATIO;
    textSize(BOX_WIDTH * 0.08);
}

function computeGlobalDepth(node) {
    if (!node.parent) {
        node.globalDepth = 0;
    } else {
        // If the parent hasn't had globalDepth computed yet, recurse on it first
        if (typeof node.parent.globalDepth === 'undefined') {
            computeGlobalDepth(node.parent);
        }
        node.globalDepth = node.parent.globalDepth + 1;
    }
}


function preprocessZoneLevels() {
    // Make sure globalDepth is set
    Object.values(nodes).forEach(node => {
        computeGlobalDepth(node);
    });

    // Find the minimum globalDepth within each zone
    let zoneMinDepth = {};
    Object.values(nodes).forEach(node => {
        if (zoneMinDepth[node.zone] === undefined || node.globalDepth < zoneMinDepth[node.zone]) {
            zoneMinDepth[node.zone] = node.globalDepth;
        }
    });

    // Subtract that min depth from each node to get a local "zoneLevel"
    Object.values(nodes).forEach(node => {
        node.zoneLevel = node.globalDepth - zoneMinDepth[node.zone];
    });
}

function layoutTree(node, minX, maxX, yOffset) {
    if (node.children.length === 0) {
        // Leaf node: center it horizontally in the [minX, maxX] slot
        node.x = (minX + maxX) / 2;
    } else {
        // Non-leaf node: divide available horizontal space among children
        const leafWeight = 1;
        const nonLeafWeight = 3;
        // Calculate a weight for each child (leaf children vs. non-leaf children)
        let weights = [];
        let totalWeight = 0;
        node.children.forEach(child => {
            let w = (child.children.length === 0) ? leafWeight : nonLeafWeight;
            weights.push(w);
            totalWeight += w;
        });

        // Walk through the children in order, distributing horizontal space
        let cumulativeWeight = 0;
        node.children.forEach((child, i) => {
            cumulativeWeight += weights[i];
            // Middle point for this child
            let childX = minX + (maxX - minX) * ((cumulativeWeight - weights[i] / 2) / totalWeight);
            // The child’s slot width
            let slotWidth = (maxX - minX) * (weights[i] / totalWeight);
            let childMinX = childX - slotWidth / 2;
            let childMaxX = childX + slotWidth / 2;

            // Recurse
            layoutTree(child, childMinX, childMaxX, yOffset);
        });

        // Position the parent node based on average of its children’s x
        let sumX = 0;
        node.children.forEach(child => { sumX += child.x; });
        node.x = sumX / node.children.length;
    }

    // Vertical position is determined by the zone level
    node.y = yOffset + node.zoneLevel * LEVEL_SPACING;
}

function ensureChildLevelSpacing(node) {
    node.children.forEach(child => {
        if (child.zone === node.zone) {
            if (child.zoneLevel <= node.zoneLevel) {
                child.zoneLevel = node.zoneLevel + 1;
            }
        }
        ensureChildLevelSpacing(child);
    });
}

function fixCrossZoneRoots() {
    // Identify nodes whose parent is in a different zone
    const crossZoneRoots = [];
    Object.values(nodes).forEach(node => {
        if (node.parent && node.parent.zone !== node.zone) {
            node.zoneLevel = 0; // treat this node as a root within its own zone
            crossZoneRoots.push(node);
        }
    });

    // Cascade updated levels to each node’s children in the same zone
    crossZoneRoots.forEach(root => {
        cascadeZoneLevels(root);
    });
}

function cascadeZoneLevels(node) {
    node.children.forEach(child => {
        if (child.zone === node.zone) {
            child.zoneLevel = node.zoneLevel + 1;
            cascadeZoneLevels(child);
        }
    });
}

function computeMultiParents() {
    // First reset each node’s children and parent references
    Object.values(nodes).forEach(node => {
        node.children = [];
        node.parent = null;      // single parent
        node.parents = [];       // array of all parents
    });

    // Build parent/child relationships
    connections.forEach(conn => {
        const fromNode = nodes[conn.from];
        const toNode = nodes[conn.to];
        if (fromNode && toNode) {
            // The single parent relationship
            //   (assign if the node doesn't have a parent yet)
            if (!toNode.parent) {
                toNode.parent = fromNode;
            }
            // Add fromNode to the array of all parents
            toNode.parents.push(fromNode);

            // Also treat the fromNode’s children as before
            fromNode.children.push(toNode);
        }
    });
}

function computeLayout() {
    computeDrawingGeometries();
    // computeChildren();
    computeMultiParents();
    preprocessZoneLevels();

    Object.values(nodes)
        .filter(n => !n.parent)
        .forEach(root => ensureChildLevelSpacing(root));

    fixCrossZoneRoots();

    // Identify root nodes (those that no one points to).
    const childIds = new Set(connections.map(conn => conn.to));
    let roots = [];
    Object.values(nodes).forEach(node => {
        if (!childIds.has(node.id)) {
            roots.push(node);
        }
    });

    // Group roots by their zone
    const rootsByZone = {};
    roots.forEach(root => {
        if (!rootsByZone[root.zone]) {
            rootsByZone[root.zone] = [];
        }
        rootsByZone[root.zone].push(root);
    });

    // Start offset for the first zone
    let currentYOffset = ZONE_START;

    // Lay out each zone in sequence
    for (let z = 1; z <= zones.length; z++) {
        // 1. Layout the subtree(s) in this zone starting at currentYOffset
        if (rootsByZone[z]) {
            rootsByZone[z].forEach(root => {
                layoutTree(root, MARGIN, width - MARGIN, currentYOffset);
            });
        }

        // 2. Find the min and max Y among the nodes in this zone
        let minY = Infinity;
        let maxY = -Infinity;
        Object.values(nodes).forEach(node => {
            if (node.zone === z) {
                if (node.y < minY) minY = node.y;
                if (node.y > maxY) maxY = node.y;
            }
        });

        // If no nodes in this zone, skip with minimal space
        if (minY === Infinity) {
            zones[z - 1].yStart = currentYOffset;
            zones[z - 1].yEnd = currentYOffset + BOX_HEIGHT + ZONE_PADDING;
            currentYOffset = zones[z - 1].yEnd + ZONE_PADDING;
            continue;
        }

        // 3. Offset all nodes in this zone so the top sits at currentYOffset + ZONE_TOP_MARGIN
        const offset = (currentYOffset + ZONE_TOP_MARGIN) - minY;
        Object.values(nodes).forEach(node => {
            if (node.zone === z) {
                node.y += offset;
            }
        });
        maxY += offset; // shift the max Y accordingly

        // 4. Record final zone boundaries
        zones[z - 1].yStart = currentYOffset;
        zones[z - 1].yEnd = maxY + BOX_HEIGHT + NODE_BOTTOM_MARGIN;

        // 5. Next zone starts below this zone’s bottom, plus a little spacing
        currentYOffset = zones[z - 1].yEnd + ZONE_PADDING;
    }
}
