// Tab Navigation
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', (e) => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    e.target.classList.add('active');
    document.getElementById(e.target.dataset.tab).classList.add('active');
    if (e.target.dataset.tab === 'templates') loadTemplates();
    if (e.target.dataset.tab === 'analytics') updateAnalytics();
  });
});

// Character count live update
document.getElementById('inputText').addEventListener('input', function() {
  document.getElementById('charCount').textContent = this.value.length;
  document.getElementById('charCountStat').textContent = this.value.length;
});

// Format email with full processing
function formatEmail() {
  const text = document.getElementById('inputText').value;
  const tone = document.getElementById('tone').value;
  const length = document.getElementById('length').value;
  const grammar = document.getElementById('grammarCheck').checked;
  const politeness = document.getElementById('politenessCheck').checked;
  const button = document.querySelector('.format-btn');
  const output = document.getElementById('outputText');
  const subjectLine = document.getElementById('subjectLine');
  const subjectDisplay = document.getElementById('subjectDisplay');

  if (!text.trim()) {
    output.value = 'Please enter some email text to format.';
    return;
  }

  const originalText = button.textContent;
  button.textContent = '⏳ Formatting...';
  button.disabled = true;

  fetch('/format', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, tone, length, grammar, politeness })
  })
  .then(res => res.json())
  .then(data => {
    output.value = data.formatted;
    subjectLine.textContent = `Subject: ${data.subject}`;
    subjectDisplay.textContent = data.subject;
    
    // Update analytics
    updateAnalytics();
    updateMetadata(data.metadata);
    
    // Animation
    output.style.animation = 'none';
    setTimeout(() => {
      output.style.animation = 'fadeIn 0.4s ease-out';
    }, 10);
  })
  .catch(error => {
    console.error('Error:', error);
    output.value = 'Error formatting email. Please try again.';
  })
  .finally(() => {
    button.textContent = originalText;
    button.disabled = false;
  });
}

// Update metadata display
function updateMetadata(metadata) {
  if (!metadata) return;
  document.getElementById('wordCount').textContent = metadata.word_count || 0;
  document.getElementById('readabilityScore').textContent = metadata.readability_score || '--';
  document.getElementById('readabilityFill').style.width = `${(metadata.readability_score || 0) / 100 * 100}%`;
  document.getElementById('politenessScore').textContent = metadata.politeness_score || '--';
  document.getElementById('politenessFill').style.width = `${(metadata.politeness_score || 0) / 100 * 100}%`;
  document.getElementById('detectedTone').textContent = metadata.detected_tone || 'Neutral';
}

// Update analytics for selected email
function updateAnalytics() {
  const output = document.getElementById('outputText');
  if (!output.value) return;

  fetch('/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: output.value })
  })
  .then(res => res.json())
  .then(data => {
    document.getElementById('readabilityScore').textContent = data.readability_score;
    document.getElementById('readabilityFill').style.width = `${(data.readability_score / 100) * 100}%`;
    document.getElementById('politenessScore').textContent = data.politeness_score;
    document.getElementById('politenessFill').style.width = `${(data.politeness_score / 100) * 100}%`;
    document.getElementById('detectedTone').textContent = data.detected_tone;
    document.getElementById('wordCount').textContent = data.word_count;
    document.getElementById('sentenceCount').textContent = data.sentence_count;
  })
  .catch(error => console.error('Analytics error:', error));
}

// Load email templates
function loadTemplates() {
  fetch('/templates')
    .then(res => res.json())
    .then(templates => {
      const grid = document.getElementById('templatesGrid');
      grid.innerHTML = '';
      
      Object.entries(templates).forEach(([name, template]) => {
        const card = document.createElement('div');
        card.className = 'template-card';
        card.innerHTML = `
          <h4>${name}</h4>
          <p>${template.template.substring(0, 100)}...</p>
          <button onclick="useTemplate('${name}', '${template.template.replace(/'/g, "\\'")}')">Use Template</button>
        `;
        grid.appendChild(card);
      });
    });
}

// Use a template
function useTemplate(name, template) {
  document.getElementById('inputText').value = template;
  document.getElementById('charCount').textContent = template.length;
  document.querySelectorAll('.tab-btn')[0].click();
  setTimeout(() => formatEmail(), 100);
}

// Copy to clipboard
function copyToClipboard() {
  const output = document.getElementById('outputText');
  const subject = document.getElementById('subjectLine').textContent.replace('Subject: ', '');
  
  if (!output.value) {
    alert('Nothing to copy. Format an email first!');
    return;
  }

  const fullEmail = `${subject}\n\n${output.value}`;
  navigator.clipboard.writeText(fullEmail).then(() => {
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = '✓ Copied!';
    setTimeout(() => { button.textContent = originalText; }, 2000);
  });
}

// Download email
function downloadEmail() {
  const output = document.getElementById('outputText');
  const subject = document.getElementById('subjectLine').textContent.replace('Subject: ', '');
  
  if (!output.value) {
    alert('Nothing to download. Format an email first!');
    return;
  }

  const content = `${subject}\n\n${output.value}`;
  const blob = new Blob([content], { type: 'text/plain' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `email_${Date.now()}.txt`;
  a.click();
}

// Save draft
function saveDraft() {
  const text = document.getElementById('inputText').value;
  const output = document.getElementById('outputText').value;
  const tone = document.getElementById('tone').value;
  const subject = document.getElementById('subjectLine').textContent;
  
  if (!text || !output) {
    alert('Please format an email first!');
    return;
  }

  const drafts = JSON.parse(localStorage.getItem('emailDrafts')) || [];
  drafts.push({
    id: Date.now(),
    timestamp: new Date().toLocaleString(),
    subject,
    tone,
    input: text,
    output,
    preview: output.substring(0, 100)
  });
  localStorage.setItem('emailDrafts', JSON.stringify(drafts));
  alert('Draft saved successfully!');
}

// View drafts
function viewDrafts() {
  const modal = document.getElementById('draftModal');
  const draftsList = document.getElementById('draftsList');
  const drafts = JSON.parse(localStorage.getItem('emailDrafts')) || [];

  draftsList.innerHTML = drafts.length === 0 ? '<p>No saved drafts</p>' : '';
  
  drafts.forEach(draft => {
    const item = document.createElement('div');
    item.className = 'draft-item';
    item.innerHTML = `
      <div class="draft-info">
        <h4>${draft.subject}</h4>
        <p>${draft.preview}...</p>
        <span class="draft-date">${draft.timestamp}</span>
      </div>
      <div class="draft-actions">
        <button onclick="loadDraft(${draft.id})" class="btn-sm">Load</button>
        <button onclick="deleteDraft(${draft.id})" class="btn-sm delete">Delete</button>
      </div>
    `;
    draftsList.appendChild(item);
  });

  modal.style.display = 'flex';
}

// Load draft
function loadDraft(id) {
  const drafts = JSON.parse(localStorage.getItem('emailDrafts')) || [];
  const draft = drafts.find(d => d.id === id);
  
  if (draft) {
    document.getElementById('inputText').value = draft.input;
    document.getElementById('outputText').value = draft.output;
    document.getElementById('subjectLine').textContent = draft.subject;
    document.getElementById('tone').value = draft.tone;
    document.getElementById('charCount').textContent = draft.input.length;
    closeDraftModal();
    updateAnalytics();
  }
}

// Delete draft
function deleteDraft(id) {
  if (confirm('Are you sure?')) {
    let drafts = JSON.parse(localStorage.getItem('emailDrafts')) || [];
    drafts = drafts.filter(d => d.id !== id);
    localStorage.setItem('emailDrafts', JSON.stringify(drafts));
    viewDrafts();
  }
}

// Modal functions
function closeDraftModal() {
  document.getElementById('draftModal').style.display = 'none';
}

// Floating panel
function toggleFloatingMenu() {
  const menu = document.getElementById('floatMenu');
  menu.style.display = menu.style.display === 'flex' ? 'none' : 'flex';
}

// Export functions
function exportAsGmail() {
  const subject = document.getElementById('subjectLine').textContent.replace('Subject: ', '');
  const body = document.getElementById('outputText').value;
  const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=&su=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  window.open(gmailUrl, '_blank');
}

function exportAsOutlook() {
  const subject = document.getElementById('subjectLine').textContent.replace('Subject: ', '');
  const body = document.getElementById('outputText').value;
  const outlookUrl = `https://outlook.office.com/mail/deeplink/compose?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  window.open(outlookUrl, '_blank');
}

function exportAsPDF() {
  const subject = document.getElementById('subjectLine').textContent;
  const output = document.getElementById('outputText').value;
  const content = `${subject}\n\n${output}`;
  
  const blob = new Blob([content], { type: 'application/pdf' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `email_${Date.now()}.pdf`;
  a.click();
}

// Utility functions
function clearInput() {
  document.getElementById('inputText').value = '';
  document.getElementById('outputText').value = '';
  document.getElementById('charCount').textContent = '0';
  document.getElementById('subjectLine').textContent = 'Subject: ';
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    formatEmail();
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    saveDraft();
  }
});

// Close modal on outside click
window.addEventListener('click', function(event) {
  const modal = document.getElementById('draftModal');
  if (event.target === modal) {
    modal.style.display = 'none';
  }
});

// Initialize
document.addEventListener('DOMContentLoaded', function() {
  const drafts = JSON.parse(localStorage.getItem('emailDrafts')) || [];
  if (drafts.length > 0) {
    console.log(`${drafts.length} drafts available`);
  }
});
