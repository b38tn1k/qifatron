// =============================
// fileStatusHandlers.js
// =============================

var currentStatus = null;

function setupButtons() {
    const buttonContainer = document.getElementById("buttonContainer");

    Object.keys(statuses).forEach((statusKey) => {
        const button = document.createElement("button");
        button.textContent = statusKey;
        button.className =
            "block w-full text-left px-4 py-2 mb-2 bg-blue-100 hover:bg-blue-200 rounded-md text-sm font-medium";
        button.style.border = "1px solid black";
        button.style.background = "white";
        button.onclick = () => {
            console.log("Clicked:", statusKey);
            handleStatusClick(statusKey);
        };
        buttonContainer.appendChild(button);
    });

    const clearButton = document.createElement("button");
    clearButton.textContent = "clear";
    clearButton.className =
        "block w-full text-left px-4 py-2 mb-2 bg-blue-100 hover:bg-blue-200 rounded-md text-sm font-medium";
    clearButton.style.border = "1px solid black";
    clearButton.style.background = "rgb(255, 200, 200)";
    clearButton.onclick = () => {
        console.log("Clicked:", "clear");
        handleStatusClick("clear");
    };
    buttonContainer.appendChild(clearButton);

    const screenshotButton = document.createElement("button");
    screenshotButton.textContent = "screenshot";
    screenshotButton.className =
        "block w-full text-left px-4 py-2 mb-2 bg-blue-100 hover:bg-blue-200 rounded-md text-sm font-medium";
    screenshotButton.style.border = "1px solid black";
    screenshotButton.style.background = "rgb(200, 255, 200)";
    screenshotButton.onclick = () => {
        console.log("Saving screenshot...");
        saveCanvas('pipeline_screenshot', 'png');
    };
    buttonContainer.appendChild(screenshotButton);
}

function handleStatusClick(statusKey) {
    if (statusKey === "clear") {
        currentStatus = null;
    }
    else {
        currentStatus = statuses[statusKey];
    }
}