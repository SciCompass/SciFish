// SciFish landing — click-to-copy install commands
(function () {
  const REPO = "https://github.com/SciCompass/SciFish";
  const INSTALL_SH = "https://scicompass.github.io/SciFish/install.sh";

  function gitCommand(skill) {
    return `git clone ${REPO} && cp -R SciFish/skills/${skill} ~/.claude/skills/`;
  }
  function curlCommand(skill) {
    return `curl -fsSL ${INSTALL_SH} | bash -s ${skill}`;
  }

  const toast = document.getElementById("toast");
  let toastTimer;
  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 1700);
  }

  async function copy(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
  }

  document.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const card = btn.closest(".card");
      const skill = card && card.dataset.skill;
      if (!skill) return;
      const method = btn.dataset.method;
      const cmd = method === "curl" ? curlCommand(skill) : gitCommand(skill);
      try {
        await copy(cmd);
        btn.classList.add("copied");
        const orig = btn.textContent;
        btn.textContent = "✓ copied";
        showToast(`Copied ${method} command for ${skill}`);
        setTimeout(() => {
          btn.classList.remove("copied");
          btn.textContent = orig;
        }, 1500);
      } catch (err) {
        showToast("Copy failed — please copy manually");
        console.error(err);
      }
    });
  });
})();
