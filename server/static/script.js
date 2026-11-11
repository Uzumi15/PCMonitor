
const computerSelect = document.getElementById("computer-select");

function updateComputerSelect(computers) {
    const selected = computerSelect.value;

    const hostnames = computers.map(computer => computer.hostname);

    computerSelect.replaceChildren();

    for (const hostname of hostnames) {
        const option = document.createElement("option");

        option.value = hostname;
        option.textContent = hostname;

        computerSelect.appendChild(option);
    }

    if (hostnames.includes(selected)) {
        computerSelect.value = selected;
    }
}

async function loadComputers() {
    const container = document.getElementById("computers");

    try {
        const response = await fetch("/metrics/latest");

        if (!response.ok) {
            throw new Error("Ошибка сервера: " + response.status);
        }

        const computers = await response.json();
        updateComputerSelect(computers);

        container.replaceChildren();

        if (computers.length === 0) {
            container.textContent = "Компьютеры пока не найдены.";
            return;
        }

        for (const computer of computers) {
            const card = document.createElement("div");
            card.className = "computer-card";

            const title = document.createElement("h3");
            title.textContent = computer.hostname;
            card.appendChild(title);
            
            const lastUpdate = new Date(computer.timestamp);
            const secondsAgo = (Date.now() - lastUpdate.getTime()) / 1000;
            const isOnline = (
                !Number.isNaN(secondsAgo) &&
                secondsAgo >= 0 &&
                secondsAgo <= 90
            );
            const status = document.createElement("p");
            status.className = isOnline ? "status online" : "status offline";
            status.textContent = isOnline
                ? "● В сети"
                : "● Нет связи";
            card.appendChild(status);
            const lastSeen = document.createElement("p");
            lastSeen.className = "last-seen";
            if (Number.isNaN(secondsAgo)) {
                lastSeen.textContent = "Время обновления неизвестно";
            } else {
                const seconds = Math.max(0, Math.floor(secondsAgo));
                if (seconds < 60) {
                    lastSeen.textContent =
                    `Последняя метрика: ${seconds} сек. назад`;
                } else if (seconds < 3600) {
                    lastSeen.textContent =
                        `Последняя метрика: ${Math.floor(seconds / 60)} мин. назад`;
                } else {
                    lastSeen.textContent =
                        `Последняя метрика: ${Math.floor(seconds / 3600)} ч. назад`;
                }
            }
            card.appendChild(lastSeen);

            const metrics = [
                ["CPU", computer.cpu_percent.toFixed(1) + "%"],
                ["RAM", computer.ram_percent.toFixed(1) + "%"],
                ["Свободный диск", computer.disk_free_gb.toFixed(1) + " GB"],
                ["Время работы", (computer.uptime_seconds / 3600).toFixed(1) + " ч"]
            ];

            for (const [name, value] of metrics) {
                const row = document.createElement("div");
                row.className = "metric";

                const label = document.createElement("span");
                label.textContent = name;

                const metricValue = document.createElement("span");
                metricValue.className = "metric-value";
                metricValue.textContent = value;

                row.append(label, metricValue);
                card.appendChild(row);
            }

            container.appendChild(card);
        }

    } catch (error) {
        console.error("Ошибка загрузки метрик:", error);
        container.textContent = "Не удалось загрузить данные компьютеров.";
    }
}

function drawChart(canvasId, metrics, field, color) {
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext("2d");

    const width = canvas.clientWidth;
    const height = canvas.clientHeight;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);

    const left = 40;
    const right = 12;
    const top = 15;
    const bottom = 30;

    const chartWidth = width - left - right;
    const chartHeight = height - top - bottom;

    if (chartWidth <= 0 || chartHeight <= 0) return;

    // Горизонтальные линии: 0%, 25%, 50%, 75%, 100%
    ctx.font = "12px Arial";
    ctx.strokeStyle = "#334155";
    ctx.fillStyle = "#94a3b8";

    for (let value = 0; value <= 100; value += 25) {
        const y = top + chartHeight * (1 - value / 100);

        ctx.beginPath();
        ctx.moveTo(left, y);
        ctx.lineTo(left + chartWidth, y);
        ctx.stroke();

        ctx.fillText(`${value}%`, 2, y + 4);
    }

    if (metrics.length === 0) {
        ctx.fillText("Нет данных", left + 10, top + 30);
        return;
    }

    // Рисуем линию нагрузки
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;

    metrics.forEach((metric, index) => {
        const x = left + (
            metrics.length === 1
                ? chartWidth / 2
                : index * chartWidth / (metrics.length - 1)
        );

        const value = Math.max(0, Math.min(100, metric[field]));
        const y = top + chartHeight * (1 - value / 100);

        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });

    ctx.stroke();
}

async function loadHistory() {
    const hostname = computerSelect.value;

    if (!hostname) return;

    try {
        const response = await fetch(
            `/metrics/history?hostname=${encodeURIComponent(hostname)}&limit=30`
        );

        if (!response.ok) {
            throw new Error("Ошибка загрузки истории");
        }

        const metrics = await response.json();

        drawChart("cpu-chart", metrics, "cpu_percent", "#38bdf8");
        drawChart("ram-chart", metrics, "ram_percent", "#22c55e");

    } catch (error) {
        console.error("Ошибка истории:", error);
    }
}


async function refreshDashboard() {
    await loadComputers();
    await loadHistory();
}

computerSelect.addEventListener("change", loadHistory);

refreshDashboard();

setInterval(refreshDashboard, 5000);
