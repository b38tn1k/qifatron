// =============================
// treeWorkers.js
// =============================

function computeChildren() {
    Object.values(nodes).forEach(node => {
        node.children = [];
        node.parent = null;
    });
    connections.forEach(conn => {
        if (nodes[conn.from] && nodes[conn.to]) {
            nodes[conn.from].children.push(nodes[conn.to]);
            nodes[conn.to].parent = nodes[conn.from];
        }
    });
}

function logNodeInfo(node) {
    console.log("----- Node Information -----");
    console.log("ID:", node.id);
    console.log("Title:", node.title);
    console.log("Type:", node.type);
    console.log("PMI:", node.PMI);
    console.log("Zone:", node.zone);
    console.log("Global Depth:", node.globalDepth !== undefined ? node.globalDepth : "Not computed");
    console.log("Zone Level:", node.zoneLevel !== undefined ? node.zoneLevel : "Not assigned");
    if (node.parent) {
        console.log("Parent ID:", node.parent.id);
    } else {
        console.log("Parent: None");
    }
    if (node.children && node.children.length > 0) {
        const childIDs = node.children.map(child => child.id);
        console.log("Children IDs:", childIDs);
    } else {
        console.log("Children: None");
    }
    if (node.x !== undefined && node.y !== undefined) {
        console.log("Position (x, y):", node.x, node.y);
    } else {
        console.log("Position: Not set");
    }
    console.log("------------------------------");
}
