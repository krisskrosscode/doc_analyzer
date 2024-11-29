document.addEventListener('DOMContentLoaded', function() {
    const customClauseRadio = document.getElementById('customClauseRadio');
    const customClauseInput = document.getElementById('customClauseInput');
    const generateButton = document.getElementById('generateButton');
    const questionsSection = document.getElementById('questionsSection');
    const questionsContent = document.getElementById('questionsContent');


    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const uploadButton = document.getElementById('uploadButton');
    const fileContent = document.getElementById('fileContent');
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const chatHistory = document.getElementById('chatHistory');
    const exportChatButton = document.getElementById('exportChat');
    const clearChatButton = document.getElementById('clearChat');
    const clearAllButton = document.getElementById('clearAll');
    const dropZone = document.getElementById('dropZone');
    const spinner = document.getElementById('spinner');

    const allowedFileTypes = ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.pdf'];

    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop functionality
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length) {
            handleFileSelect({ target: { files: files } });
        }
    });

    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
            if (allowedFileTypes.includes(fileExtension)) {
                uploadButton.textContent = 'Upload ' + file.name;
                uploadButton.disabled = false;
                fileInput.files = e.target.files;  // Update the file input
            } else {
                uploadButton.textContent = 'Invalid file type';
                uploadButton.disabled = true;
                alert('Please select a valid file type: ' + allowedFileTypes.join(', '));
            }
        } else {
            uploadButton.textContent = 'Upload';
            uploadButton.disabled = false;
        }
    }

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(uploadForm);

        // Check if there's existing chat history
        if (chatHistory.innerHTML.trim() !== '') {
            const userChoice = await showUploadConfirmation();
            if (userChoice === 'cancel') {
                return;
            }
            formData.append('action', userChoice);
        } else {
            formData.append('action', 'upload');
        }

        try {
            setLoading(true);
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            if (data.error) {
                alert(`Error: ${data.error}`);
                fileContent.textContent = '';
            } else {
                fileContent.textContent = data.content;
                localStorage.setItem('fileContent', data.content); // Store file content in localStorage
                if (data.chatHistory) {
                    updateChatHistory(data.chatHistory);
                }
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while uploading the file.');
            fileContent.textContent = '';
        } finally {
            setLoading(false);
        }
    });
    // Show/hide custom clause input based on radio selection
    customClauseRadio.addEventListener('change', function() {
        customClauseInput.style.display = this.checked ? 'block' : 'none';
        customClauseInput.disabled = !this.checked;
    });

    generateButton.addEventListener('click', function() {
        const selectedRadio = document.querySelector('input[name="clause"]:checked');
        
        if (!selectedRadio) {
            alert('Please select a clause');
            return;
        }

        let selectedClause = selectedRadio.value;
        
        // If custom clause is selected, get the value from the input
        if (selectedRadio.id === 'customClauseRadio') {
            selectedClause = customClauseInput.value;
            if (!selectedClause.trim()) {
                alert('Please enter a custom clause');
                return;
            }
        }

        // Show loading state
        questionsSection.style.display = 'block';
        questionsContent.innerHTML = '<p>Generating questions...</p>';

        // Create FormData object
        const formData = new FormData();
        formData.append('clause', selectedClause);

        // Send the selected clause to the backend
        fetch('/report_rag', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                questionsContent.innerHTML = `<p class="error">${data.error}</p>`;
            } else {
                // Format the response as a numbered list
                const formattedResponse = data.response
                    .split('\n')
                    .filter(line => line.trim())
                    .map(line => `<li>${line}</li>`)
                    .join('');
                
                questionsContent.innerHTML = `
                    <div class="response">
                        <p><strong>Selected Clause:</strong> ${selectedClause}</p>
                        <p><strong>Generated Questions:</strong></p>
                        <ol>${formattedResponse}</ol>
                    </div>`;
            }
        })
        .catch(error => {
            questionsContent.innerHTML = `<p class="error">Error: ${error.message}</p>`;
            console.error('Error:', error);
        });
    });
});