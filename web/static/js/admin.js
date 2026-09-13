(() => {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const format = new Intl.NumberFormat();

  // Bulk selection: count, highlight, select-all and shift-click ranges. One
  // form holds a selection at a time so the floating bars never stack.
  const bulkForms = [...document.querySelectorAll("form[data-bulk]")];
  const refreshers = new Map();
  const clearOthers = (keep) => {
    for (const other of bulkForms) {
      if (other === keep) continue;
      let changed = false;
      for (const box of other.querySelectorAll('input[name="ids"]')) {
        if (box.checked) changed = true;
        box.checked = false;
      }
      if (changed) refreshers.get(other)?.();
    }
  };
  for (const form of bulkForms) {
    const boxes = [...form.querySelectorAll('input[name="ids"]')];
    const all = form.querySelector("[data-select-all]");
    const bar = form.querySelector(".bulk-bar");
    const count = form.querySelector("[data-bulk-count]");
    let last = null;

    if (bar) bar.classList.add("is-idle");

    const refresh = () => {
      const ticked = boxes.filter((box) => box.checked);
      if (ticked.length > 0) clearOthers(form);
      for (const box of boxes) box.closest("tr")?.classList.toggle("is-selected", box.checked);
      if (count) count.textContent = format.format(ticked.length);
      if (bar) bar.classList.toggle("is-active", ticked.length > 0);
      if (all) {
        all.checked = ticked.length > 0 && ticked.length === boxes.length;
        all.indeterminate = ticked.length > 0 && ticked.length < boxes.length;
      }
    };

    all?.addEventListener("change", () => {
      for (const box of boxes) box.checked = all.checked;
      refresh();
    });

    boxes.forEach((box, index) => {
      box.addEventListener("click", (event) => {
        if (event.shiftKey && last !== null) {
          const [from, to] = [Math.min(last, index), Math.max(last, index)];
          for (let i = from; i <= to; i += 1) boxes[i].checked = box.checked;
        }
        last = index;
        refresh();
      });
    });

    for (const row of form.querySelectorAll("tbody tr")) {
      row.addEventListener("click", (event) => {
        if (event.target.closest("a, input, button, label, select")) return;
        const box = row.querySelector('input[name="ids"]');
        if (!box) return;
        box.checked = !box.checked;
        last = boxes.indexOf(box);
        refresh();
      });
    }

    refreshers.set(form, refresh);
    refresh();
  }

  // Destructive buttons confirm through one shared dialog.
  const dialog = document.getElementById("confirm");
  if (dialog) {
    const text = dialog.querySelector("[data-confirm-text]");
    let pending = null;

    document.addEventListener("click", (event) => {
      const button = event.target.closest("[data-confirm]");
      if (!button || !button.form) return;
      event.preventDefault();
      pending = button;
      text.textContent = button.dataset.confirm;
      dialog.showModal();
    });

    dialog.querySelector("[data-confirm-ok]").addEventListener("click", () => {
      dialog.close();
      if (pending) pending.form.requestSubmit(pending);
      pending = null;
    });
    dialog.querySelector("[data-confirm-cancel]").addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
  }

  // Filters that apply as soon as they change; sliders that show their value.
  for (const select of document.querySelectorAll("select[data-autosubmit]")) {
    select.addEventListener("change", () => select.form?.requestSubmit());
  }
  for (const range of document.querySelectorAll("input[data-range]")) {
    const output = range.closest("label")?.querySelector("[data-range-output]");
    range.addEventListener("input", () => {
      if (output) output.textContent = range.value;
    });
  }

  // Numbers count up from zero when the page opens.
  if (!reduceMotion) {
    for (const node of document.querySelectorAll("[data-count-up]")) {
      const target = Number(node.dataset.value);
      if (!Number.isFinite(target) || target === 0) continue;
      const started = performance.now();
      const duration = 650;
      const step = (now) => {
        const progress = Math.min((now - started) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        node.textContent = format.format(Math.round(target * eased));
        if (progress < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    }
  }

  // Keyboard: "/" focuses the search box, "g" then a rail key jumps there.
  const typing = () => {
    const active = document.activeElement;
    return active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA" || active.tagName === "SELECT");
  };
  let chord = 0;
  document.addEventListener("keydown", (event) => {
    if (typing() || event.ctrlKey || event.metaKey || event.altKey || dialog?.open) return;
    if (event.key === "/") {
      const search = document.querySelector("[data-search]");
      if (search) {
        event.preventDefault();
        search.focus();
        search.select();
      }
      return;
    }
    if (event.key === "g") {
      chord = performance.now();
      return;
    }
    if (performance.now() - chord < 900) {
      const link = document.querySelector(`.rail a[data-key="${event.key}"]`);
      if (link) window.location.assign(link.getAttribute("href"));
      chord = 0;
    }
  });

  // Live status: poll the JSON probe and animate the tiles.
  const grid = document.querySelector("[data-poll-url]");
  if (grid) {
    const seconds = Math.max(Number(grid.dataset.pollSeconds) || 10, 3);
    const checked = document.querySelector("[data-checked-at]");
    const liveDot = document.querySelector("[data-live-dot]");
    let stopped = false;

    const tween = (node, to) => {
      const from = Number(node.textContent) || 0;
      if (reduceMotion || Number.isNaN(from)) {
        node.textContent = Math.round(to);
        return;
      }
      const started = performance.now();
      const step = (now) => {
        const progress = Math.min((now - started) / 400, 1);
        node.textContent = Math.round(from + (to - from) * progress);
        if (progress < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };

    const apply = (payload) => {
      for (const tile of payload.tiles) {
        const node = grid.querySelector(`[data-key="${tile.key}"]`);
        if (!node) continue;
        node.classList.remove("up", "down", "unknown");
        node.classList.add(tile.state);
        const dot = node.querySelector("[data-dot]");
        if (dot) dot.className = `dot ${tile.state}`;
        const ms = node.querySelector("[data-ms]");
        if (ms) {
          if (tile.latency_ms === null) ms.textContent = "–";
          else tween(ms, tile.latency_ms);
        }
        const facts = node.querySelector("[data-facts]");
        if (facts) {
          facts.replaceChildren(
            ...tile.facts.flatMap(([key, value]) => {
              const dt = document.createElement("dt");
              dt.textContent = key;
              const dd = document.createElement("dd");
              dd.textContent = value;
              return [dt, dd];
            }),
          );
        }
      }
      if (checked) checked.textContent = payload.checked_at.replace("T", " ").slice(0, 16);
    };

    const poll = async () => {
      if (stopped) return;
      if (document.hidden) {
        window.setTimeout(poll, seconds * 1000);
        return;
      }
      try {
        const answer = await fetch(grid.dataset.pollUrl, { credentials: "same-origin", cache: "no-store" });
        if (!answer.ok || answer.redirected) throw new Error("stopped");
        apply(await answer.json());
      } catch {
        stopped = true;
        if (liveDot) liveDot.className = "dot unknown";
        for (const dot of grid.querySelectorAll("[data-dot]")) dot.className = "dot unknown";
        return;
      }
      window.setTimeout(poll, seconds * 1000);
    };

    window.setTimeout(poll, seconds * 1000);
  }
})();
