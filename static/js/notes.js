// Notes specific JavaScript functionality

let currentNoteId = null;

// Helper function to show loading state
function showLoading(button) {
    if (!button) return;
    button.disabled = true;
    button.dataset.originalText = button.innerHTML;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
}

// Helper function to hide loading state
function hideLoading(button) {
    if (!button) return;
    button.disabled = false;
    if (button.dataset.originalText) {
        button.innerHTML = button.dataset.originalText;
    }
}

// Helper function to show alerts
function showAlert(message, type = 'info') {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Add note functionality
document.getElementById('addNoteForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    console.log('Add note form submitted');
    
    const submitBtn = this.querySelector('button[type="submit"]');
    const titleInput = document.getElementById('addNoteTitle');
    const contentInput = document.getElementById('addNoteContent');
    
    // Validate title
    if (!titleInput.value.trim()) {
        showAlert('Please enter a title for your note', 'warning');
        titleInput.focus();
        return;
    }
    
    showLoading(submitBtn);
    
    try {
        const formData = new FormData(this);
        
        console.log('Sending data to /add_note');
        console.log('Title:', titleInput.value);
        console.log('Content:', contentInput.value);
        
        const response = await fetch('/add_note', {
            method: 'POST',
            body: formData
        });
        
        console.log('Response status:', response.status);
        
        const result = await response.json();
        console.log('Response data:', result);
        
        if (result.success) {
            showAlert(result.message || 'Note added successfully!', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addNoteModal'));
            if (modal) {
                modal.hide();
            }
            
            // Reset form
            this.reset();
            document.getElementById('addImagePreview').innerHTML = '';
            
            // Reload page to show new note
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showAlert(result.message || 'Failed to add note', 'danger');
        }
    } catch (error) {
        console.error('Add note error:', error);
        showAlert('An error occurred while adding the note. Please try again.', 'danger');
    } finally {
        hideLoading(submitBtn);
    }
});

// Edit note functionality
document.getElementById('editNoteForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    console.log('Edit note form submitted');
    
    const noteId = document.getElementById('editNoteId').value;
    const submitBtn = this.querySelector('button[type="submit"]');
    const titleInput = document.getElementById('editNoteTitle');
    
    // Validate title
    if (!titleInput.value.trim()) {
        showAlert('Please enter a title for your note', 'warning');
        titleInput.focus();
        return;
    }
    
    showLoading(submitBtn);
    
    try {
        const formData = new FormData(this);
        
        console.log('Sending data to /edit_note/' + noteId);
        
        const response = await fetch(`/edit_note/${noteId}`, {
            method: 'POST',
            body: formData
        });
        
        console.log('Response status:', response.status);
        
        const result = await response.json();
        console.log('Response data:', result);
        
        if (result.success) {
            showAlert(result.message || 'Note updated successfully!', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('editNoteModal'));
            if (modal) {
                modal.hide();
            }
            
            // Reload page to show updated note
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showAlert(result.message || 'Failed to update note', 'danger');
        }
    } catch (error) {
        console.error('Edit note error:', error);
        showAlert('An error occurred while updating the note. Please try again.', 'danger');
    } finally {
        hideLoading(submitBtn);
    }
});

// View note function
async function viewNote(noteId) {
    console.log('Viewing note:', noteId);
    
    try {
        const response = await fetch(`/get_note/${noteId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const note = await response.json();
        console.log('Note data:', note);
        
        // Set title
        document.getElementById('viewNoteTitle').textContent = note.title;
        
        // Set content
        const contentDiv = document.getElementById('viewNoteContent');
        if (note.content) {
            contentDiv.innerHTML = `<p style="white-space: pre-wrap;">${escapeHtml(note.content)}</p>`;
        } else {
            contentDiv.innerHTML = '<em class="text-muted">No content</em>';
        }
        
        // Set image if exists
        const imageDiv = document.getElementById('viewNoteImage');
        if (note.image_filename) {
            imageDiv.innerHTML = `
                <img src="/static/uploads/${note.image_filename}" 
                     class="img-fluid rounded mb-3" alt="Note image" 
                     style="max-height: 300px; width: 100%; object-fit: cover;">
            `;
        } else {
            imageDiv.innerHTML = '';
        }
        
        // Set dates
        document.getElementById('viewNoteDates').innerHTML = `
            <small>
                <strong>Created:</strong> ${note.created_at}<br>
                <strong>Updated:</strong> ${note.updated_at}
            </small>
        `;
        
        // Set up edit button
        document.getElementById('editFromViewBtn').onclick = function() {
            const viewModal = bootstrap.Modal.getInstance(document.getElementById('viewNoteModal'));
            if (viewModal) {
                viewModal.hide();
            }
            setTimeout(() => {
                editNote(noteId);
            }, 300);
        };
        
        currentNoteId = noteId;
        
    } catch (error) {
        console.error('View note error:', error);
        showAlert('Failed to load note. Please try again.', 'danger');
    }
}

// Edit note function
async function editNote(noteId) {
    console.log('Editing note:', noteId);
    
    try {
        const response = await fetch(`/get_note/${noteId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const note = await response.json();
        console.log('Note data for editing:', note);
        
        // Set form values
        document.getElementById('editNoteId').value = note.id;
        document.getElementById('editNoteTitle').value = note.title;
        document.getElementById('editNoteContent').value = note.content || '';
        
        // Show current image if exists
        const imagePreview = document.getElementById('editImagePreview');
        if (note.image_filename) {
            imagePreview.innerHTML = `
                <div class="current-image mb-2">
                    <p class="text-muted mb-2">Current image:</p>
                    <img src="/static/uploads/${note.image_filename}" 
                         class="img-fluid rounded" alt="Current image" 
                         style="max-height: 200px; object-fit: cover;">
                </div>
            `;
        } else {
            imagePreview.innerHTML = '';
        }
        
        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('editNoteModal'));
        modal.show();
        
    } catch (error) {
        console.error('Edit note function error:', error);
        showAlert('Failed to load note for editing. Please try again.', 'danger');
    }
}

// Delete note function
async function deleteNote(noteId) {
    console.log('Deleting note:', noteId);
    
    if (!confirm('Are you sure you want to delete this note? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/delete_note/${noteId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        console.log('Delete result:', result);
        
        if (response.ok && result.success) {
            showAlert(result.message || 'Note deleted successfully!', 'success');
            
            // Reload page to update the notes list
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showAlert(result.message || 'Failed to delete note', 'danger');
        }
    } catch (error) {
        console.error('Delete note error:', error);
        showAlert('An error occurred while deleting the note. Please try again.', 'danger');
    }
}

// Image preview function
function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    
    if (!input.files || !input.files[0]) {
        return;
    }
    
    const file = input.files[0];
    
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        showAlert('Please select a valid image file (JPG, PNG, GIF, BMP, WEBP)', 'danger');
        input.value = '';
        return;
    }
    
    // Validate file size (16MB max)
    const maxSize = 16 * 1024 * 1024; // 16MB
    if (file.size > maxSize) {
        showAlert('File size must be less than 16MB', 'danger');
        input.value = '';
        return;
    }
    
    // For edit mode, remove current image display when new image is selected
    if (previewId === 'editImagePreview') {
        const currentImage = preview.querySelector('.current-image');
        if (currentImage) {
            currentImage.remove();
        }
    }
    
    // Show preview
    const reader = new FileReader();
    reader.onload = function(e) {
        const previewDiv = document.createElement('div');
        previewDiv.className = 'new-image-preview';
        previewDiv.innerHTML = `
            <p class="text-muted mb-2">New image preview:</p>
            <img src="${e.target.result}" class="img-fluid rounded" 
                 alt="Image preview" style="max-height: 200px; object-fit: cover;">
        `;
        
        // Remove any existing preview
        const existingPreview = preview.querySelector('.new-image-preview');
        if (existingPreview) {
            existingPreview.remove();
        }
        
        preview.appendChild(previewDiv);
    };
    reader.readAsDataURL(file);
}

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Clear form when modals are hidden
document.getElementById('addNoteModal').addEventListener('hidden.bs.modal', function () {
    const form = document.getElementById('addNoteForm');
    form.reset();
    document.getElementById('addImagePreview').innerHTML = '';
});

document.getElementById('editNoteModal').addEventListener('hidden.bs.modal', function () {
    const form = document.getElementById('editNoteForm');
    form.reset();
    document.getElementById('editImagePreview').innerHTML = '';
});

// Focus on title input when add modal is shown
document.getElementById('addNoteModal').addEventListener('shown.bs.modal', function () {
    document.getElementById('addNoteTitle').focus();
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+N or Cmd+N to add new note
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        const addNoteModal = new bootstrap.Modal(document.getElementById('addNoteModal'));
        addNoteModal.show();
    }
});

// Make functions available globally for onclick handlers
window.viewNote = viewNote;
window.editNote = editNote;
window.deleteNote = deleteNote;
window.previewImage = previewImage;

// Log when script is loaded
console.log('notes.js loaded successfully');