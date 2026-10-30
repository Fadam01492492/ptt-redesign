// 批踢踢 Redesign — 前端互動
(function () {
  // 手機版側邊選單
  const btn = document.getElementById("menuBtn");
  const scrim = document.getElementById("scrim");
  if (btn) btn.addEventListener("click", () => document.body.classList.toggle("nav-open"));
  if (scrim) scrim.addEventListener("click", () => document.body.classList.remove("nav-open"));

  // 通知自動關閉
  document.querySelectorAll(".toast").forEach((t) => {
    t.querySelector(".toast-x")?.addEventListener("click", () => t.remove());
    setTimeout(() => t.remove(), 5000);
  });

  // 密碼顯示 / 隱藏
  document.querySelectorAll(".pw-toggle").forEach((b) => {
    b.addEventListener("click", () => {
      const input = document.getElementById(b.dataset.target);
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      b.textContent = show ? "隱藏" : "顯示";
    });
  });

  // 複製文章連結
  document.querySelectorAll("[data-copy]").forEach((b) => {
    b.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(b.dataset.copy); b.textContent = "✓ 已複製"; }
      catch { b.textContent = "複製失敗"; }
      setTimeout(() => (b.textContent = "🔗 複製連結"), 1800);
    });
  });

  // 收藏看板：不重新整理頁面（fetch）
  const csrf = document.cookie.split("; ").find((c) => c.startsWith("csrftoken="))?.split("=")[1];
  document.querySelectorAll(".fav-btn[data-board]").forEach((b) => {
    b.addEventListener("click", async (e) => {
      e.preventDefault();
      const form = b.closest("form");
      try {
        const res = await fetch(form.action, {
          method: "POST",
          headers: { "X-CSRFToken": csrf, "X-Requested-With": "fetch" },
          credentials: "same-origin",
        });
        if (!res.ok) throw new Error();
        const data = await res.json();
        const label = b.textContent.includes("看板") ? "收藏看板" : "收藏";
        b.classList.toggle("on", data.favorited);
        b.textContent = data.favorited ? `★ 已${label}` : `☆ ${label}`;
      } catch {
        form.submit(); // 失敗時退回一般表單送出
      }
    });
  });

  // 推文字數提示
  const ci = document.querySelector(".comment-form input[name=content]");
  if (ci) ci.addEventListener("input", () => {
    ci.style.borderColor = ci.value.length > 90 ? "var(--boo)" : "";
  });
})();
