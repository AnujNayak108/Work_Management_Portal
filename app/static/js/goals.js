/* Goal form — dynamic rows, real-time weightage validation */
document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('goals-container');
  const addBtn = document.getElementById('add-goal-btn');
  const weightageText = document.getElementById('weightage-text');
  const weightageFill = document.getElementById('weightage-fill');
  const submitBtn = document.getElementById('submit-goals-btn');
  const MAX_GOALS = 8;

  if (!container) return;

  let goalIndex = container.querySelectorAll('.goal-row').length;

  function createGoalRow(index, data = {}) {
    const row = document.createElement('div');
    row.className = 'goal-row';
    row.dataset.index = index;
    const isShared = data.is_shared || false;
    const readonlyAttr = isShared ? 'readonly' : '';

    row.innerHTML = `
      <div class="goal-row-header">
        <span class="goal-number">GOAL ${index + 1}</span>
        <span class="remove-goal" onclick="removeGoal(this)" title="Remove">&times;</span>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Thrust Area</label>
          <input type="text" name="goals-${index}-thrust_area" class="form-control" 
            value="${data.thrust_area || ''}" required ${readonlyAttr}>
        </div>
        <div class="form-group">
          <label class="form-label">Goal Title</label>
          <input type="text" name="goals-${index}-title" class="form-control" 
            value="${data.title || ''}" required ${readonlyAttr}>
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Description</label>
        <textarea name="goals-${index}-description" class="form-control">${data.description || ''}</textarea>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Unit of Measurement</label>
          <select name="goals-${index}-unit_type" class="form-control" onchange="toggleTargetFields(this)" ${readonlyAttr}>
            <option value="numeric" ${data.unit_type === 'numeric' ? 'selected' : ''}>Numeric</option>
            <option value="percentage" ${data.unit_type === 'percentage' ? 'selected' : ''}>Percentage (%)</option>
            <option value="timeline" ${data.unit_type === 'timeline' ? 'selected' : ''}>Timeline</option>
            <option value="zero_based" ${data.unit_type === 'zero_based' ? 'selected' : ''}>Zero-based</option>
          </select>
        </div>
        <div class="form-group target-value-group">
          <label class="form-label">Target Value</label>
          <input type="number" name="goals-${index}-target_value" class="form-control" 
            value="${data.target_value || ''}" step="any" ${readonlyAttr}>
        </div>
        <div class="form-group target-date-group hidden">
          <label class="form-label">Target Date</label>
          <input type="date" name="goals-${index}-target_date" class="form-control" 
            value="${data.target_date || ''}">
        </div>
        <div class="form-group">
          <label class="form-label">Weightage (%)</label>
          <input type="number" name="goals-${index}-weightage" class="form-control weightage-input" 
            value="${data.weightage || '10'}" min="10" max="100" required
            oninput="updateWeightage()">
        </div>
      </div>
      <input type="hidden" name="goals-${index}-is_shared" value="${isShared}">
      <input type="hidden" name="goals-${index}-shared_goal_id" value="${data.shared_goal_id || ''}">
    `;
    return row;
  }

  if (addBtn) {
    addBtn.addEventListener('click', () => {
      if (goalIndex >= MAX_GOALS) {
        showToast('Maximum 8 goals allowed.', 'warning');
        return;
      }
      container.appendChild(createGoalRow(goalIndex));
      goalIndex++;
      updateWeightage();
      updateGoalNumbers();
    });
  }

  // Add first row if empty
  if (goalIndex === 0 && addBtn) {
    container.appendChild(createGoalRow(0));
    goalIndex = 1;
  }

  updateWeightage();
});

function removeGoal(el) {
  const row = el.closest('.goal-row');
  if (document.querySelectorAll('.goal-row').length <= 1) {
    showToast('At least one goal is required.', 'warning');
    return;
  }
  row.style.animation = 'fadeIn 0.3s ease reverse';
  setTimeout(() => { row.remove(); reindexGoals(); updateWeightage(); updateGoalNumbers(); }, 300);
}

function reindexGoals() {
  document.querySelectorAll('.goal-row').forEach((row, i) => {
    row.dataset.index = i;
    row.querySelectorAll('[name]').forEach(input => {
      input.name = input.name.replace(/goals-\d+-/, `goals-${i}-`);
    });
  });
}

function updateGoalNumbers() {
  document.querySelectorAll('.goal-row .goal-number').forEach((el, i) => {
    el.textContent = `GOAL ${i + 1}`;
  });
}

function updateWeightage() {
  const inputs = document.querySelectorAll('.weightage-input');
  const fill = document.getElementById('weightage-fill');
  const text = document.getElementById('weightage-text');
  if (!fill || !text) return;

  let total = 0;
  inputs.forEach(i => total += parseInt(i.value) || 0);

  fill.style.width = Math.min(total, 100) + '%';
  fill.className = 'weightage-fill ' + (total === 100 ? 'valid' : 'invalid');
  text.textContent = total + '%';
  text.style.color = total === 100 ? 'var(--emerald)' : 'var(--rose)';
}

function toggleTargetFields(select) {
  const row = select.closest('.goal-row');
  const valGroup = row.querySelector('.target-value-group');
  const dateGroup = row.querySelector('.target-date-group');
  if (select.value === 'timeline') {
    valGroup.classList.add('hidden');
    dateGroup.classList.remove('hidden');
  } else if (select.value === 'zero_based') {
    valGroup.classList.add('hidden');
    dateGroup.classList.add('hidden');
  } else {
    valGroup.classList.remove('hidden');
    dateGroup.classList.add('hidden');
  }
}

function addSharedGoal(sg) {
  const container = document.getElementById('goals-container');
  const rows = container.querySelectorAll('.goal-row');
  if (rows.length >= 8) { showToast('Maximum 8 goals.', 'warning'); return; }
  const idx = rows.length;
  const row = document.createElement('div');
  row.className = 'goal-row';
  row.style.borderColor = 'var(--accent)';
  // Similar to createGoalRow but with shared data pre-filled
  const event = new CustomEvent('addSharedGoal', { detail: { ...sg, index: idx } });
  document.dispatchEvent(event);
}
