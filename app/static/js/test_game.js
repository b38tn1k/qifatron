const paddleWidth = 100;
const paddleHeight = 20;
const ballSize = 15;
let paddleX;
let ballX, ballY;
let ballSpeedX, ballSpeedY;
let score = 0;
let gameOver = false;

function setup() {
    const canvas = createCanvas(600, 400);
    canvas.parent("game-container");
    paddleX = width / 2 - paddleWidth / 2;
    ballX = width / 2;
    ballY = height / 2;
    ballSpeedX = random([-3, 3]);
    ballSpeedY = -3;
}

function draw() {
    background(200);
    if (gameOver) {
        console.log("GAME OVER");
        document.getElementById('game-over').classList.remove('hidden');
        document.getElementById('final-score').textContent = score;
        noLoop();
        return;
    }

    // Draw paddle
    rect(paddleX, height - paddleHeight - 10, paddleWidth, paddleHeight);

    // Draw ball
    ellipse(ballX, ballY, ballSize);

    // Update ball position
    ballX += ballSpeedX;
    ballY += ballSpeedY;

    // Ball collisions with walls
    if (ballX <= 0 || ballX >= width) {
        ballSpeedX *= -1;
    }

    if (ballY <= 0) {
        ballSpeedY *= -1;
    }

    // Ball collision with paddle
    if (
        ballY + ballSize / 2 >= height - paddleHeight - 10 &&
        ballX > paddleX &&
        ballX < paddleX + paddleWidth
    ) {
        ballSpeedY *= -1;
        score++;
    }

    // Game over condition
    if (ballY > height) {
        gameOver = true;
    }

    // Paddle movement
    if (keyIsDown(LEFT_ARROW)) {
        paddleX -= 5;
    }
    if (keyIsDown(RIGHT_ARROW)) {
        paddleX += 5;
    }

    // Constrain paddle within canvas
    paddleX = constrain(paddleX, 0, width - paddleWidth);

    // Display score
    textSize(16);
    textAlign(LEFT, TOP);
    text(`Score: ${score}`, 10, 10);
}

document.getElementById('player-name-form').addEventListener('submit', function (e) {
    e.preventDefault();
    const playerName = document.getElementById('player-name').value;
    sendScoreToServer(playerName, score);
});

function sendScoreToServer(name, score) {
    fetch('/testing/add-score', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: name, score: score }),
    })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            window.location.reload();
        })
        .catch(error => console.error('Error:', error));
}

function fetchHighScores() {
    fetch('/testing/get-scores')
        .then(response => response.json())
        .then(scores => {
            const scoresList = document.getElementById('high-scores');
            scoresList.innerHTML = '';
            scores.forEach(score => {
                const scoreItem = document.createElement('div');
                scoreItem.className = 'list-group-item';
                scoreItem.textContent = `${score.name}: ${score.score}`;
                scoresList.appendChild(scoreItem);
            });
        })
        .catch(error => console.error('Error fetching scores:', error));
}

// Fetch high scores on page load
fetchHighScores();