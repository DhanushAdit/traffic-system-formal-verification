/**
 * Canvas visualizer: POST /api/reset and POST /api/step return the same JSON
 * your Python simulation builds (cars, depots, signals, metrics).
 */
(function () {
  const canvas = document.getElementById("grid");
  const statusEl = document.getElementById("status");
  const stepNumEl = document.getElementById("step-num");
  const cumulativeEl = document.getElementById("cumulative");
  const reportEl = document.getElementById("report");
  const congestionEl = document.getElementById("congestion");
  const signalTimingEl = document.getElementById("signal-timing");
  const btnStep = document.getElementById("btn-step");
  const btnReset = document.getElementById("btn-reset");
  const btnAuto = document.getElementById("btn-auto");
  const btnStop = document.getElementById("btn-stop");
  const intervalInput = document.getElementById("interval");

  if (!canvas || !canvas.getContext) {
    statusEl.textContent = "No canvas.";
    statusEl.classList.add("err");
    return;
  }
  const ctx = canvas.getContext("2d");
  const W = canvas.width;
  const H = canvas.height;
  const padL = 100;
  const padR = 72;
  const padT = 64;
  const padB = 64;
  const cellX = (W - padL - padR) / 2;
  const cellY = (H - padT - padB) / 2;
  /** One lane width: distance from road centerline to outer curb. */
  const LANE_WIDTH = Math.min(cellX, cellY) * 0.14;

  let autoTimer = null;

  function gridToPx(ix, iy) {
    return { x: padL + ix * cellX, y: padT + (GRID_SIZE - 1 - iy) * cellY };
  }

  /** Unit tangent and right-hand perpendicular (screen px) from a → b. */
  function segGeometry(a, b) {
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const len = Math.hypot(dx, dy) || 1;
    const ux = dx / len;
    const uy = dy / len;
    const rx = -uy;
    const ry = ux;
    return { ux, uy, rx, ry, len };
  }

  function gridDeltaToDir(dgx, dgy) {
    if (dgx === 1 && dgy === 0) return "E";
    if (dgx === -1 && dgy === 0) return "W";
    if (dgx === 0 && dgy === 1) return "N";
    if (dgx === 0 && dgy === -1) return "S";
    return "E";
  }

  const GRID_SIZE = 3;

  /**
   * Approach directions that have a road into (ix, iy), matching traffic_infra Dir /
   * green_approach (one bead per incident edge).
   */
  function approachDirsAtIntersection(ix, iy) {
    const dirs = [];
    if (ix + 1 < GRID_SIZE) dirs.push("E");
    if (ix - 1 >= 0) dirs.push("W");
    if (iy + 1 < GRID_SIZE) dirs.push("N");
    if (iy - 1 >= 0) dirs.push("S");
    return dirs;
  }

  /**
   * Pixel offset from intersection center toward the road that carries this approach
   * (same neighbor as traffic_infra: E→(ix+1,iy), W→(ix-1,iy), N→(ix,iy+1), S→(ix,iy-1)).
   */
  function lightOffsetTowardRoad(ix, iy, dir, dist) {
    let nx = ix;
    let ny = iy;
    if (dir === "E") nx = ix + 1;
    else if (dir === "W") nx = ix - 1;
    else if (dir === "N") ny = iy + 1;
    else if (dir === "S") ny = iy - 1;
    const p = gridToPx(ix, iy);
    const q = gridToPx(nx, ny);
    const dx = q.x - p.x;
    const dy = q.y - p.y;
    const len = Math.hypot(dx, dy) || 1;
    return [(dx / len) * dist, (dy / len) * dist];
  }

  function post(path) {
    return fetch(path, {
      method: "POST",
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    }).then((r) => {
      if (!r.ok) return r.text().then((t) => Promise.reject(new Error(t || r.statusText)));
      return r.json();
    });
  }

  function setStatus(ok, msg) {
    statusEl.textContent = msg;
    statusEl.classList.toggle("err", !ok);
  }

  function drawTwoLaneRoad(a, b) {
    const { rx, ry } = segGeometry(a, b);
    const h = LANE_WIDTH;
    ctx.fillStyle = "#4b5563";
    ctx.strokeStyle = "#374151";
    ctx.lineWidth = 1;
    ctx.lineJoin = "round";
    ctx.beginPath();
    ctx.moveTo(a.x + rx * h, a.y + ry * h);
    ctx.lineTo(b.x + rx * h, b.y + ry * h);
    ctx.lineTo(b.x - rx * h, b.y - ry * h);
    ctx.lineTo(a.x - rx * h, a.y - ry * h);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    ctx.strokeStyle = "rgba(250, 204, 21, 0.9)";
    ctx.lineWidth = 2;
    ctx.lineCap = "butt";
    ctx.setLineDash([7, 9]);
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  function drawRoads() {
    for (let x = 0; x < GRID_SIZE; x++) {
      for (let y = 0; y < GRID_SIZE; y++) {
        if (x + 1 < GRID_SIZE) drawTwoLaneRoad(gridToPx(x, y), gridToPx(x + 1, y));
        if (y + 1 < GRID_SIZE) drawTwoLaneRoad(gridToPx(x, y), gridToPx(x, y + 1));
      }
    }
  }

  function drawFeederToA(depots) {
    const a = depots && depots.find((d) => d.label === "A");
    if (!a || !a.adj || !a.outward) return;
    const outward = { N: [0, -1], E: [1, 0], S: [0, 1], W: [-1, 0] };
    const d = outward[a.outward];
    if (!d) return;
    const base = gridToPx(a.adj[0], a.adj[1]);
    const stand = Math.min(cellX, cellY) * 0.16;
    const box = a.box != null ? Number(a.box) : 0.34;
    const hw = (box * cellX) / 2;
    const cx = base.x + d[0] * stand;
    const cy = base.y + d[1] * stand;
    const east = { x: cx + hw, y: cy };
    const joint = gridToPx(a.adj[0], a.adj[1]);
    const inset = Math.min(cellX, cellY) * 0.06;
    drawTwoLaneRoad({ x: east.x + inset, y: east.y }, { x: joint.x - inset, y: joint.y });
  }

  function drawDepots(depots) {
    if (!depots) return;
    const outward = { N: [0, -1], E: [1, 0], S: [0, 1], W: [-1, 0] };
    const stand = Math.min(cellX, cellY) * 0.16;
    depots.forEach((d) => {
      if (d.kind === "corner_label" && d.adj) {
        const p = gridToPx(d.adj[0], d.adj[1]);
        ctx.fillStyle = "rgba(255,255,255,0.9)";
        ctx.strokeStyle = "#cbd5e1";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(p.x, p.y - 24, 13, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        ctx.font = "bold 14px sans-serif";
        ctx.fillStyle = "#0f172a";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(d.label, p.x, p.y - 24);
        return;
      }
      if (d.kind !== "start_square" || !d.adj || !d.outward) return;
      const base = gridToPx(d.adj[0], d.adj[1]);
      const [ox, oy] = outward[d.outward];
      const cx = base.x + ox * stand;
      const cy = base.y + oy * stand;
      const box = d.box != null ? Number(d.box) : 0.34;
      const hw = (box * cellX) / 2;
      const hh = (box * cellY) / 2;
      ctx.fillStyle = "rgba(13, 148, 136, 0.9)";
      ctx.strokeStyle = "#0f766e";
      ctx.lineWidth = 2;
      ctx.fillRect(cx - hw, cy - hh, hw * 2, hh * 2);
      ctx.strokeRect(cx - hw, cy - hh, hw * 2, hh * 2);
      ctx.fillStyle = "#042f2e";
      ctx.font = "bold 14px sans-serif";
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      ctx.fillText("A", cx - hw - 6, cy);
      ctx.textAlign = "center";
      ctx.fillStyle = "#ccfbf1";
      ctx.font = "9px sans-serif";
      ctx.fillText("START", cx, cy + 10);
      ctx.fillStyle = "#0f172a";
      ctx.font = "bold 12px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("A", cx, cy - 8);
    });
  }

  function drawLights(signalsMap) {
    if (!signalsMap) return;
    const off = 18;
    const order = ["N", "E", "S", "W"];
    for (let x = 0; x < GRID_SIZE; x++) {
      for (let y = 0; y < GRID_SIZE; y++) {
        const active = new Set(approachDirsAtIntersection(x, y));
        const green = signalsMap[`${x},${y}`];
        const p = gridToPx(x, y);
        order.forEach((dir) => {
          if (!active.has(dir)) return;
          const [dx, dy] = lightOffsetTowardRoad(x, y, dir, off);
          const qx = p.x + dx;
          const qy = p.y + dy;
          const isG = green === dir;
          ctx.fillStyle = isG ? "#16a34a" : "#dc2626";
          ctx.strokeStyle = isG ? "#14532d" : "#7f1d1d";
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.arc(qx, qy, 4, 0, Math.PI * 2);
          ctx.fill();
          ctx.stroke();
        });
      }
    }
  }

  function drawDots() {
    for (let x = 0; x < GRID_SIZE; x++) {
      for (let y = 0; y < GRID_SIZE; y++) {
        const p = gridToPx(x, y);
        ctx.fillStyle = "#334155";
        ctx.strokeStyle = "#0f172a";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 8, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      }
    }
  }

  function carPx(car, slots) {
    const n = Math.max(2, slots | 0);
    const f = car.edge.frm;
    const t = car.edge.to;
    // Render each slot at its midpoint so slot 29 is still visibly before the node.
    const u = (car.slot + 0.5) / n;
    const gx = f[0] + (t[0] - f[0]) * u;
    const gy = f[1] + (t[1] - f[1]) * u;
    const Pa = gridToPx(f[0], f[1]);
    const Pb = gridToPx(t[0], t[1]);
    const { rx, ry } = segGeometry(Pa, Pb);
    const fwd = gridDeltaToDir(t[0] - f[0], t[1] - f[1]);
    const sign = car.driving_dir === fwd ? 1 : -1;
    const laneCenterOff = LANE_WIDTH * 0.48;
    const base = gridToPx(gx, gy);
    return {
      x: base.x + sign * rx * laneCenterOff,
      y: base.y + sign * ry * laneCenterOff,
    };
  }

  function drawCars(cars, slots) {
    const list = Object.values(cars || {});
    list.forEach((car, i) => {
      const p = carPx(car, slots);
      const hue = (i * 61) % 360;
      ctx.fillStyle = `hsl(${hue} 75% 48%)`;
      ctx.strokeStyle = "#0f172a";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 10, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#fff";
      ctx.font = "bold 9px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText((car.car_id || "?").slice(0, 4), p.x, p.y);
    });
  }

  function render(state) {
    ctx.fillStyle = "#f1f5f9";
    ctx.fillRect(0, 0, W, H);
    drawRoads();
    drawFeederToA(state.depots);
    drawDepots(state.depots);
    drawLights(state.signals_all_intersections);
    drawDots();
    drawCars(state.cars, state.slots_per_segment || 30);
    ctx.fillStyle = "#64748b";
    ctx.font = "11px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText(
      "This canvas renders Python snapshots from /api/step. Cars move one slot per step and may cross only on the single green approach at an intersection.",
      12,
      H - 10,
    );
  }

  function updatePanel(state) {
    stepNumEl.textContent = String(state.step_index ?? 0);
    const c = state.cumulative || {};
    const rows = [
      ["Collisions", c.collision_count],
      ["Red-light violations", c.red_light_violations],
      ["Illegal direction", c.illegal_direction_count],
      ["U-turns", c.u_turn_count],
      ["Intersection crossing issues", c.intersection_crossing_violations],
    ];
    cumulativeEl.innerHTML = rows
      .map(([k, v]) => `<li><strong>${k}:</strong> ${v}</li>`)
      .join("");
    reportEl.textContent =
      state.last_report == null ? "—" : JSON.stringify(state.last_report, null, 2);
    const cg = state.congestion || {};
    congestionEl.textContent =
      Object.keys(cg).length === 0 ? "—" : JSON.stringify(cg, null, 2);
    signalTimingEl.textContent = JSON.stringify(state.signal_timing || {}, null, 2);
  }

  function applyState(data) {
    if (data.type === "state") {
      render(data);
      updatePanel(data);
    }
  }

  function stopAuto(silent) {
    if (autoTimer) {
      clearInterval(autoTimer);
      autoTimer = null;
    }
    btnStop.disabled = true;
    btnAuto.disabled = false;
    if (!silent && !statusEl.classList.contains("err")) {
      setStatus(true, "Paused");
    }
  }

  function startAuto() {
    const ms = Math.max(200, parseInt(intervalInput.value, 10) || 1200);
    if (autoTimer) clearInterval(autoTimer);
    btnStop.disabled = false;
    btnAuto.disabled = true;
    autoTimer = setInterval(() => {
      post("/api/step")
        .then(applyState)
        .catch((e) => {
          setStatus(false, e.message);
          stopAuto();
        });
    }, ms);
  }

  function loadInitial() {
    setStatus(true, "Requesting initial state…");
    return post("/api/reset")
      .then((data) => {
        applyState(data);
        setStatus(true, "Paused · " + location.origin);
        btnStep.disabled = false;
        btnReset.disabled = false;
        btnAuto.disabled = false;
        btnStop.disabled = true;
      })
      .catch((e) => {
        setStatus(false, "Server: " + e.message + " — run python -m traffic_infra.web_app");
        btnStep.disabled = true;
        btnReset.disabled = true;
        btnAuto.disabled = true;
        btnStop.disabled = true;
      });
  }

  btnStep.addEventListener("click", () => {
    post("/api/step")
      .then(applyState)
      .catch((e) => setStatus(false, e.message));
  });

  btnReset.addEventListener("click", () => {
    stopAuto(true);
    post("/api/reset")
      .then((data) => {
        applyState(data);
        setStatus(true, "Paused · " + location.origin);
        btnAuto.disabled = false;
        btnStop.disabled = true;
      })
      .catch((e) => setStatus(false, e.message));
  });

  btnAuto.addEventListener("click", () => {
    setStatus(true, "Running · " + location.origin);
    startAuto();
  });

  btnStop.addEventListener("click", () => {
    stopAuto();
  });

  btnStep.disabled = true;
  btnReset.disabled = true;
  btnAuto.disabled = true;
  loadInitial();
})();
