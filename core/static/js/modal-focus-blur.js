(function(){
  // Add/remove `modal-opened` on <body> when any modal overlay/box becomes visible.
  // Watches elements with common modal class names: modal-overlay, logout-modal-overlay, modal, modal-box, modal-overlay-style, etc.
  function isElementVisible(el){
    if(!el) return false;
    try{
      var style = window.getComputedStyle(el);
      return style && style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
    }catch(e){ return false; }
  }

  function anyModalOpen(){
    // Only treat an explicit modal overlay/dialog as a modal-open signal.
    // This avoids false positives from unrelated elements that happen to be visible.
    // Check for overlays with the explicit 'open' or 'logout-open' class.
    if (document.querySelector('.modal-overlay.open, .logout-modal-overlay.logout-open, .modal-overlay.logout-open, .logout-modal-overlay.open')) {
      return true;
    }

    // Check dialogs which use aria-hidden to indicate visibility.
    var dialogs = document.querySelectorAll('[role="dialog"]');
    for (var k = 0; k < dialogs.length; k++) {
      var d = dialogs[k];
      var aria = d.getAttribute('aria-hidden');
      if (aria === 'false') return true;
      var cls = d.classList;
      if (cls && (cls.contains('open') || cls.contains('logout-open'))) return true;
    }

    return false;
  }

  function updateBodyClass(){
    if(anyModalOpen()) document.body.classList.add('modal-opened');
    else document.body.classList.remove('modal-opened');
  }

  document.addEventListener('DOMContentLoaded', function(){
    // ensure no stale class on load
    document.body.classList.remove('modal-opened');

    // initial check
    updateBodyClass();

    // observe subtree for class or style changes that may open/close modals
    var observer = new MutationObserver(function(mutations){
      // small debounce
      clearTimeout(window.__modalBlurTimeout);
      window.__modalBlurTimeout = setTimeout(updateBodyClass, 50);
    });

    observer.observe(document.documentElement || document.body, {
      attributes: true,
      childList: true,
      attributeFilter: ['class','style','aria-hidden'],
      subtree: true
    });

    // also periodically re-check in case some scripts use inline styles without mutations
    setInterval(updateBodyClass, 400);

    // clean up on unload
    window.addEventListener('unload', function(){ observer.disconnect(); });
  });
})();
