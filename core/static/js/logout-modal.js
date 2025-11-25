(function(){
  document.addEventListener('DOMContentLoaded', function(){
    var modal = document.getElementById('logoutModal');
    if(!modal) return;
    var confirmBtn = modal.querySelector('.logout-confirm');
    var cancelBtn = modal.querySelector('.logout-cancel');
    var logoutHref = null;

    function openModal(href){
      logoutHref = href;
      modal.classList.add('logout-open');
      modal.setAttribute('aria-hidden','false');
    }
    function closeModal(){
      logoutHref = null;
      modal.classList.remove('logout-open');
      modal.setAttribute('aria-hidden','true');
    }

    document.querySelectorAll('a.logout-link').forEach(function(link){
      link.addEventListener('click', function(e){
        // allow middle-click / ctrl-click to keep original behavior
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.button === 1) return;
        e.preventDefault();
        openModal(link.getAttribute('href'));
      });
    });

    cancelBtn.addEventListener('click', function(){ closeModal(); });
    confirmBtn.addEventListener('click', function(){
      if(logoutHref){ window.location.href = logoutHref; }
    });

    // close on Escape
    document.addEventListener('keydown', function(e){ if(e.key === 'Escape') closeModal(); });
    // close when clicking outside the modal box
    modal.addEventListener('click', function(e){ if(e.target === modal) closeModal(); });
  });
})();
