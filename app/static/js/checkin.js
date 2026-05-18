/* Check-in interactions */
document.addEventListener('DOMContentLoaded', () => {
  // Inline edit toggle
  document.querySelectorAll('.inline-edit-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const row = btn.closest('tr') || btn.closest('.goal-row');
      const fields = row.querySelectorAll('.inline-field');
      const displays = row.querySelectorAll('.inline-display');
      fields.forEach(f => f.classList.toggle('hidden'));
      displays.forEach(d => d.classList.toggle('hidden'));
      btn.textContent = btn.textContent === 'Edit' ? 'Cancel' : 'Edit';
    });
  });
});
