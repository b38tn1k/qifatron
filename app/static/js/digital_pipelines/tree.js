// =============================
// treeModel.js
// =============================

// Model data (zones, nodes, connections)
const zones = [
    { name: "3D Experience (Design Engineer)" },
    { name: "3D Experience (PMI/DX Engineer)" },
    { name: "MBDVidia (DX Validation)" },
    { name: "Calypso & KOTEM (Quality Engineering)" }
];

// Define the nodes with positions, type, title, PMI flag, and zone.
const nodes = {
    // Zone 1 nodes
    1: { id: 1, title: "3D Experience", type: "Software", PMI: false, proprietary: true, zone: 1, version: "2022 hotfix9", failure_mode: false },
    2: { id: 2, title: "3dxml", type: "File Package", PMI: false, proprietary: true, zone: 1, failure_mode: false, components: [".3Dxml", ".CATProduct"]},

    // Zone 2 nodes
    3: { id: 3, title: "3D Experience", type: "Software", PMI: false, proprietary: true, zone: 2, version: "2025 hotfix1.1", failure_mode: false },
    4: { id: 4, title: "3dxml", type: "File Format", PMI: true, proprietary: true, zone: 2, failure_mode: false },
    5: { id: 5, title: ".CATProduct", type: "File Format", PMI: true, proprietary: true, zone: 2, failure_mode: false, version: "CATIA v5 r2016" },
    6: { id: 6, title: "STEP242", type: "File Format", PMI: true, proprietary: false, zone: 2, version: "ed3", failure_mode: false },

    // Zone 3 nodes
    7: { id: 7, title: "Unsupported", type: "File Format", PMI: false, proprietary: false, zone: 3, failure_mode: true },
    8: { id: 8, title: ".CATProduct", type: "File Format", PMI: true, proprietary: true, zone: 3, failure_mode: false },
    9: { id: 9, title: "STEP242", type: "File Format", PMI: true, proprietary: false, zone: 3, failure_mode: false },
    10: { id: 10, title: "QIF", type: "File Format", PMI: true, proprietary: false, zone: 3, failure_mode: false, version: "+ Dimensions" },
    11: { id: 11, title: "QIF", type: "File Format", PMI: true, proprietary: false, zone: 3, failure_mode: false, version: "+ Dimensions" },

    // Zone 4 nodes
    12: { id: 12, title: "Kotem", type: "Software", PMI: false, proprietary: true, zone: 4, failure_mode: false },
    13: { id: 13, title: "Calypso", type: "Software", PMI: false, proprietary: true, zone: 4, failure_mode: false },
    14: { id: 14, title: "Inspection Data", type: "File Package", PMI: true, proprietary: true, zone: 4, components: ["QIF + Measurement Plan", "Point Cloud"], failure_mode: false }
};

// Define the connections between nodes.
const connections = [
    // Zone 1 connections
    { from: 1, to: 2, type: "strong" },
    { from: 2, to: 3, type: "strong" },

    // Zone 2 connections
    { from: 3, to: 6, type: "strong" },
    { from: 3, to: 4, type: "weak" },
    { from: 3, to: 5, type: "weak" },
    { from: 4, to: 7, type: "weak" },
    { from: 5, to: 8, type: "weak" },
    { from: 6, to: 9, type: "strong" },

    // Zone 3 connections
    { from: 8, to: 10, type: "weak" },
    { from: 9, to: 11, type: "strong" },

    // Cross-zone connections from Zone 3 to Zone 4
    { from: 11, to: 13, type: "strong" },
    { from: 10, to: 13, type: "weak" },
    { from: 13, to: 14, type: "strong" },
    { from: 14, to: 12, type: "strong" }
];
