document.addEventListener('DOMContentLoaded', () => {
    const agentNameEl = document.getElementById('agent-name');
    const agentStatusEl = document.getElementById('agent-status');
    const notesListEl = document.getElementById('notes-list');
    const noteContentEl = document.getElementById('note-content-display');

    const converter = new showdown.Converter();

    async function fetchStatus() {
        try {
            const response = await fetch('/status');
            const data = await response.json();
            agentNameEl.textContent = data.name || 'Agent';
            agentStatusEl.textContent = data.status;
        } catch (error) {
            console.error('Error fetching status:', error);
            agentStatusEl.textContent = 'Error';
        }
    }

    async function fetchNotes() {
        try {
            const response = await fetch('/notes');
            const notes = await response.json();
            renderNotesList(notes);
        } catch (error) {
            console.error('Error fetching notes:', error);
        }
    }

    async function fetchNoteContent(filename) {
        try {
            const response = await fetch(`/notes/${filename}`);
            const data = await response.json();
            const htmlContent = converter.makeHtml(data.content);
            noteContentEl.innerHTML = htmlContent;
        } catch (error) {
            console.error('Error fetching note content:', error);
            noteContentEl.innerHTML = '<p class="placeholder">Failed to load note.</p>';
        }
    }

    function renderNotesList(notes) {
        notesListEl.innerHTML = '';
        notes.forEach(note => {
            const li = document.createElement('li');
            li.textContent = note;
            li.dataset.filename = note;
            li.addEventListener('click', () => {
                // Remove active class from all other items
                document.querySelectorAll('#notes-list li').forEach(item => item.classList.remove('active'));
                // Add active class to the clicked item
                li.classList.add('active');
                fetchNoteContent(note);
            });
            notesListEl.appendChild(li);
        });
    }

    // Initial data fetch
    fetchStatus();
    fetchNotes();

    // Poll for status updates every 2 seconds
    setInterval(fetchStatus, 2000);
    // Refresh notes list every 10 seconds to catch new notes
    setInterval(fetchNotes, 10000);
});
