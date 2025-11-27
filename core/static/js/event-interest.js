function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.interest-btn').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      const eventId = this.getAttribute('data-event-id');
      if (!eventId) return;
      const url = `/event/${eventId}/toggle-interest/`;
      const csrftoken = getCookie('csrftoken');
      fetch(url, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'X-CSRFToken': csrftoken,
          'X-Requested-With': 'XMLHttpRequest',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      }).then(r => r.json())
      .then(data => {
        if (!data) return;
        const interested = data.interested;
        const done = data.done;
        const count = data.interest_count;
        const star = btn.querySelector('.star');
        if (interested) {
          if (star) star.textContent = '★';
          btn.setAttribute('aria-pressed', 'true');
        } else {
          if (star) star.textContent = '☆';
          btn.setAttribute('aria-pressed', 'false');
        }
        // update nearby count if present
        const countEl = btn.parentElement.querySelector('.interest-count');
        if (countEl) {
          countEl.textContent = count;
        } else if (done && btn.parentElement && !countEl) {
          // If event is done but count element not present, create it
          const span = document.createElement('span');
          span.className = 'interest-count';
          span.textContent = count;
          btn.parentElement.appendChild(span);
        }
        // Update right-panel events attended summary if present and event is done
        if (done) {
          const summaryEl = document.getElementById('events-attended-count');
          if (summaryEl) {
            // parse current value as int (fallback to 0)
            const current = parseInt(summaryEl.textContent || '0', 10) || 0;
            if (interested) {
              summaryEl.textContent = current + 1;
            } else {
              summaryEl.textContent = Math.max(0, current - 1);
            }
          }
        }
      }).catch(err => console.error('Error toggling interest', err));
    });
  });
});
