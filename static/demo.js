(() => {
  const VALID_ROLES = new Set(["brigadier", "inspector"]);
  const DEFAULT_ROLE = "brigadier";
  const STORAGE_KEY = "siteflow.demoPerspective";
  const entry = document.querySelector("[data-demo-entry]");
  const taskTool = document.querySelector("[data-task-tool]");
  const startButton = document.querySelector("[data-start-demo]");
  const entryRoleButtons = [...document.querySelectorAll("[data-entry-role]")];
  const roleButtons = [...document.querySelectorAll("[data-role-select]")];
  const fileInputs = [...document.querySelectorAll("[data-file-input]")];
  let selectedEntryRole = DEFAULT_ROLE;

  if (!entry || !taskTool || !startButton) return;

  const readRole = () => {
    try {
      const storedRole = sessionStorage.getItem(STORAGE_KEY);
      return VALID_ROLES.has(storedRole) ? storedRole : null;
    } catch (_) {
      return null;
    }
  };

  const saveRole = (role) => {
    try {
      sessionStorage.setItem(STORAGE_KEY, role);
    } catch (_) {
      // The role remains usable for this page when session storage is unavailable.
    }
  };

  const syncButtons = (role) => {
    roleButtons.forEach((button) => {
      const active = button.dataset.roleSelect === role;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    });
  };

  const applyRole = (role, persist = true) => {
    const nextRole = VALID_ROLES.has(role) ? role : DEFAULT_ROLE;
    taskTool.dataset.demoRole = nextRole;
    syncButtons(nextRole);
    if (persist) saveRole(nextRole);
  };

  const openTaskTool = (role) => {
    applyRole(role);
    entry.hidden = true;
    taskTool.hidden = false;
    taskTool.querySelector("h1")?.focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: "auto" });
  };

  entryRoleButtons.forEach((button) => {
    button.addEventListener("click", () => {
      selectedEntryRole = VALID_ROLES.has(button.dataset.entryRole) ? button.dataset.entryRole : DEFAULT_ROLE;
      entryRoleButtons.forEach((candidate) => {
        const active = candidate === button;
        candidate.classList.toggle("is-active", active);
        candidate.setAttribute("aria-pressed", String(active));
      });
    });
  });

  roleButtons.forEach((button) => {
    button.addEventListener("click", () => applyRole(button.dataset.roleSelect));
  });

  startButton.addEventListener("click", () => openTaskTool(selectedEntryRole));

  fileInputs.forEach((input) => {
    input.addEventListener("change", () => {
      const filename = input.files?.[0]?.name || input.dataset.empty;
      const output = input.parentElement?.querySelector(".file-picker-name");
      if (output) output.textContent = filename;
    });
  });

  const storedRole = readRole();
  if (storedRole) {
    openTaskTool(storedRole);
  } else {
    entry.hidden = false;
    taskTool.hidden = true;
    applyRole(DEFAULT_ROLE, false);
  }
})();
