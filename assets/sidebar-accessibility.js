/* Progressive keyboard support for the shared mobile Reflex sidebar. */
(() => {
  const install = () => {
    if (window.__vittaSidebarKeyboardInstalled) return;
    window.__vittaSidebarKeyboardInstalled = true;

    const mobile = window.matchMedia('(max-width: 1050px)');
    const getShell = () => document.querySelector('.vitta-shell');
    const getDrawer = () => getShell()?.querySelector('.vitta-sidebar');
    const isOpen = () => mobile.matches && Boolean(getShell()?.classList.contains('is-mobile-nav-open'));
    let wasOpen = false;
    let opener = null;
    let observedShell = null;

    const syncFocus = () => {
      const open = isOpen();
      if (open === wasOpen) return;
      wasOpen = open;
      if (open) {
        opener = document.querySelector('.vitta-hamburger-mobile');
        requestAnimationFrame(() => {
          if (isOpen()) getDrawer()?.querySelector('.vitta-sidebar-close')?.focus();
        });
      } else {
        const returnTarget = opener;
        requestAnimationFrame(() => {
          if (mobile.matches && returnTarget?.isConnected) returnTarget.focus();
        });
      }
    };

    const shellObserver = new MutationObserver(syncFocus);
    const bindShell = () => {
      const shell = getShell();
      if (shell !== observedShell) {
        shellObserver.disconnect();
        observedShell = shell;
        if (shell) shellObserver.observe(shell, { attributes: true, attributeFilter: ['class'] });
      }
      syncFocus();
    };

    document.addEventListener('keydown', (event) => {
      if (!isOpen()) return;
      const drawer = getDrawer();
      if (!drawer) return;

      if (event.key === 'Escape') {
        event.preventDefault();
        drawer.querySelector('.vitta-sidebar-close')?.click();
        return;
      }
      if (event.key !== 'Tab') return;

      const items = [...drawer.querySelectorAll('a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])')]
        .filter((item) => item.getClientRects().length > 0);
      if (!items.length) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && (document.activeElement === first || !drawer.contains(document.activeElement))) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (document.activeElement === last || !drawer.contains(document.activeElement))) {
        event.preventDefault();
        first.focus();
      }
    }, true);

    const bodyObserver = new MutationObserver(bindShell);
    bodyObserver.observe(document.body, { childList: true, subtree: true });
    window.addEventListener('resize', syncFocus, { passive: true });
    bindShell();
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', install, { once: true });
  } else {
    install();
  }
})();
