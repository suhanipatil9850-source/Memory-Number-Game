from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


PAGE = """<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Memory Number Game</title>
    <style>
        :root {
            color-scheme: dark;
            --bg: #0b1020;
            --panel: rgba(15, 23, 42, 0.88);
            --panel-border: rgba(148, 163, 184, 0.16);
            --text: #e2e8f0;
            --muted: #94a3b8;
            --accent: #38bdf8;
            --accent-2: #f59e0b;
            --good: #22c55e;
            --bad: #ef4444;
        }

        * { box-sizing: border-box; }

        body {
            margin: 0;
            min-height: 100vh;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color: var(--text);
            background:
                radial-gradient(circle at top left, rgba(56, 189, 248, 0.25), transparent 30%),
                radial-gradient(circle at bottom right, rgba(245, 158, 11, 0.18), transparent 28%),
                linear-gradient(160deg, #050816 0%, #0b1020 55%, #111827 100%);
            display: grid;
            place-items: center;
            padding: 24px;
        }

        .card {
            width: min(720px, 100%);
            border: 1px solid var(--panel-border);
            background: var(--panel);
            backdrop-filter: blur(14px);
            border-radius: 24px;
            box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
            padding: 28px;
        }

        .eyebrow {
            color: var(--accent);
            font-size: 0.85rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin: 0 0 10px;
        }

        h1 {
            margin: 0;
            font-size: clamp(2rem, 4vw, 3.25rem);
            line-height: 1.05;
        }

        .subtext {
            margin: 12px 0 24px;
            color: var(--muted);
            max-width: 60ch;
        }

        .grid {
            display: grid;
            gap: 18px;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            margin-bottom: 18px;
        }

        .stat {
            border: 1px solid var(--panel-border);
            border-radius: 18px;
            padding: 16px;
            background: rgba(15, 23, 42, 0.45);
        }

        .stat span {
            display: block;
            color: var(--muted);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 8px;
        }

        .stat strong {
            font-size: 1.5rem;
        }

        .board {
            border: 1px solid var(--panel-border);
            border-radius: 20px;
            padding: 24px;
            background: rgba(2, 6, 23, 0.35);
            margin-bottom: 18px;
        }

        .number {
            min-height: 84px;
            display: grid;
            place-items: center;
            font-size: clamp(2rem, 9vw, 4.5rem);
            letter-spacing: 0.28em;
            font-weight: 800;
            color: white;
            text-shadow: 0 0 24px rgba(56, 189, 248, 0.35);
            user-select: none;
            padding-left: 0.28em;
            text-align: center;
        }

        .number.hidden {
            letter-spacing: 0.12em;
            color: transparent;
            text-shadow: none;
        }

        .controls {
            display: grid;
            gap: 12px;
            grid-template-columns: minmax(0, 1fr) auto;
            align-items: center;
        }

        input {
            width: 100%;
            border: 1px solid var(--panel-border);
            border-radius: 14px;
            background: rgba(15, 23, 42, 0.7);
            color: var(--text);
            padding: 14px 16px;
            font-size: 1rem;
            outline: none;
        }

        input:focus {
            border-color: rgba(56, 189, 248, 0.85);
            box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.15);
        }

        button {
            border: 0;
            border-radius: 14px;
            padding: 14px 18px;
            font-weight: 700;
            font-size: 0.98rem;
            color: #03111f;
            background: linear-gradient(135deg, #7dd3fc, #38bdf8);
            cursor: pointer;
            transition: transform 140ms ease, filter 140ms ease;
        }

        button:hover { transform: translateY(-1px); filter: brightness(1.03); }
        button:active { transform: translateY(0); }
        button:disabled { opacity: 0.55; cursor: not-allowed; transform: none; }

        .message {
            min-height: 28px;
            margin-top: 14px;
            font-weight: 600;
        }

        .good { color: var(--good); }
        .bad { color: var(--bad); }
        .hint { color: var(--muted); margin-top: 10px; font-size: 0.95rem; }

        @media (max-width: 700px) {
            .card { padding: 20px; }
            .grid { grid-template-columns: 1fr; }
            .controls { grid-template-columns: 1fr; }
            button { width: 100%; }
        }
    </style>
</head>
<body>
    <main class="card">
        <p class="eyebrow">Memory Number Game</p>
        <h1>Train your short-term memory</h1>
        <p class="subtext">Watch the number, memorize it before it disappears, then type it back exactly. Each correct answer adds one digit to the next round.</p>

        <section class="grid">
            <div class="stat"><span>Level</span><strong id="level">1</strong></div>
            <div class="stat"><span>Best streak</span><strong id="best">0</strong></div>
            <div class="stat"><span>Round state</span><strong id="state">Ready</strong></div>
        </section>

        <section class="board">
            <div class="number" id="number">Press Start</div>
            <div class="controls">
                <input id="guess" inputmode="numeric" autocomplete="off" placeholder="Type the number here" disabled>
                <button id="start">Start Round</button>
            </div>
            <div class="message" id="message"></div>
            <div class="hint">You get 2 seconds to memorize the number.</div>
        </section>
    </main>

    <script>
        const levelEl = document.getElementById("level");
        const bestEl = document.getElementById("best");
        const stateEl = document.getElementById("state");
        const numberEl = document.getElementById("number");
        const guessEl = document.getElementById("guess");
        const startBtn = document.getElementById("start");
        const messageEl = document.getElementById("message");

        let level = 1;
        let best = 0;
        let currentNumber = "";
        let hideTimer = null;
        let roundActive = false;

        function makeNumber(length) {
            let value = "";
            for (let index = 0; index < length; index += 1) {
                value += Math.floor(Math.random() * 10);
            }
            return value;
        }

        function setMessage(text, kind = "") {
            messageEl.textContent = text;
            messageEl.className = `message ${kind}`.trim();
        }

        function setState(text) {
            stateEl.textContent = text;
        }

        function startRound() {
            if (roundActive) return;

            roundActive = true;
            currentNumber = makeNumber(level);
            guessEl.value = "";
            guessEl.disabled = true;
            startBtn.disabled = true;
            startBtn.textContent = "Memorize...";
            numberEl.textContent = currentNumber;
            numberEl.classList.remove("hidden");
            setState("Memorize");
            setMessage("Look carefully.");

            clearTimeout(hideTimer);
            hideTimer = setTimeout(() => {
                numberEl.textContent = "••••••";
                numberEl.classList.add("hidden");
                guessEl.disabled = false;
                guessEl.focus();
                startBtn.disabled = false;
                startBtn.textContent = "Check Answer";
                setState("Answer");
                setMessage("Type the number and press Enter or Check Answer.");
            }, 2000);
        }

        function checkAnswer() {
            if (!roundActive || guessEl.disabled) return;

            const guess = guessEl.value.trim();
            if (!guess) {
                setMessage("Enter a number first.", "bad");
                return;
            }

            if (guess === currentNumber) {
                best = Math.max(best, level);
                level += 1;
                levelEl.textContent = level;
                bestEl.textContent = best;
                setMessage(`Correct. Next round will use ${level} digits.`, "good");
                setState("Ready");
                numberEl.textContent = "Press Start";
                numberEl.classList.remove("hidden");
                roundActive = false;
                startBtn.textContent = "Start Round";
            } else {
                setMessage(`Wrong. The number was ${currentNumber}. Game reset.`, "bad");
                setState("Reset");
                best = Math.max(best, level - 1);
                bestEl.textContent = best;
                level = 1;
                levelEl.textContent = level;
                roundActive = false;
                numberEl.textContent = "Press Start";
                numberEl.classList.remove("hidden");
                startBtn.textContent = "Start Round";
            }

            guessEl.disabled = true;
            startBtn.disabled = false;
            currentNumber = "";
        }

        startBtn.addEventListener("click", () => {
            if (guessEl.disabled) {
                startRound();
            } else {
                checkAnswer();
            }
        });

        guessEl.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                checkAnswer();
            }
        });

        setMessage("Press Start Round to begin.");
    </script>
</body>
</html>"""


class GameHandler(BaseHTTPRequestHandler):
        def do_GET(self):
                page = PAGE.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(page)))
                self.end_headers()
                self.wfile.write(page)

        def log_message(self, format, *args):
                return


def main():
        host = "127.0.0.1"
        port = 8000
        server = ThreadingHTTPServer((host, port), GameHandler)
        print(f"Serving Memory Number Game at http://{host}:{port}")
        server.serve_forever()


if __name__ == "__main__":
        main()