/* Progressive enhancement for the existing Reflex sidebar.
 * The server keeps navigation/RBAC state; this only manages mobile dialog focus. */
(() => {
  if (window.__vittaShellNavigationInitialized) return;
  window.__vittaShellNavigationInitialized = true;

  const media = window.matchMedia("(max-width: 1050px)");
  let opened = false;
  let returnFocus = null;
  let previousBodyOverflow = "";
  let previousHtmlOverflow = "";
  let lastMain = null;
  let lastSidebar = null;

  const nodes = () => {
    const shell = document.querySelector(".vitta-shell");
    return {
      shell,
      sidebar: shell?.querySelector("#vitta-sidebar"),
      main: shell?.querySelector(".vitta-main"),
      close: shell?.querySelector(".vitta-sidebar-close"),
      trigger: shell?.querySelector(".vitta-hamburger-mobile"),
    };
  };

  const isOpen = ({ shell }) =>
    Boolean(media.matches && shell?.classList.contains("is-mobile-nav-open"));

  function sync() {
    const view = nodes();
    const nextOpen = isOpen(view);
    if (nextOpen && !opened) {
      opened = true;
      returnFocus = document.activeElement;
      previousBodyOverflow = document.body.style.overflow;
      previousHtmlOverflow = document.documentElement.style.overflow;
      document.body.style.overflow = "hidden";
      document.documentElement.style.overflow = "hidden";
      lastMain = view.main;
      lastSidebar = view.sidebar;
      if (lastMain) lastMain.inert = true;
      if (lastSidebar) {
        lastSidebar.setAttribute("role", "dialog");
        lastSidebar.setAttribute("aria-modal", "true");
      }
      requestAnimationFrame(() => nodes().close?.focus());
    } else if (!nextOpen && opened) {
      opened = false;
      document.body.style.overflow = previousBodyOverflow;
      document.documentElement.style.overflow = previousHtmlOverflow;
      if (lastMain) lastMain.inert = false;
      if (lastSidebar) {
        lastSidebar.setAttribute("role", "complementary");
        lastSidebar.removeAttribute("aria-modal");
      }
      view.sidebar?.removeAttribute("aria-modal");
      lastMain = null;
      lastSidebar = null;
      const focus = view.trigger || returnFocus;
      if (focus?.isConnected) requestAnimationFrame(() => focus.focus());
      returnFocus = null;
    } else if (nextOpen && view.main && view.main !== lastMain) {
      if (lastMain) lastMain.inert = false;
      lastMain = view.main;
      lastMain.inert = true;
    }
  }

  document.addEventListener("keydown", (event) => {
    const view = nodes();
    if (!isOpen(view) || !view.sidebar) return;
    if (event.key === "Escape") {
      event.preventDefault();
      view.close?.click();
      return;
    }
    if (event.key !== "Tab") return;
    const controls = [...view.sidebar.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), [tabindex="0"]'
    )].filter((node) => node.getClientRects().length > 0);
    if (!controls.length) {
      event.preventDefault();
      view.close?.focus();
      return;
    }
    const first = controls[0];
    const last = controls[controls.length - 1];
    if (event.shiftKey && (document.activeElement === first || !view.sidebar.contains(document.activeElement))) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && (document.activeElement === last || !view.sidebar.contains(document.activeElement))) {
      event.preventDefault();
      first.focus();
    }
  });

  const observer = new MutationObserver(sync);
  observer.observe(document.body, {
    attributes: true,
    attributeFilter: ["class"],
    childList: true,
    subtree: true,
  });
  media.addEventListener("change", sync);
  window.addEventListener("pagehide", () => {
    if (opened) {
      document.body.style.overflow = previousBodyOverflow;
      document.documentElement.style.overflow = previousHtmlOverflow;
      if (lastMain) lastMain.inert = false;
    }
  });
  sync();
})();
