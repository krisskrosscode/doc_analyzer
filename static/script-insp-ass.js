document.addEventListener('DOMContentLoaded', function() {
    const customClauseRadio = document.getElementById('customClauseRadio');
    const customClauseInput = document.getElementById('customClauseInput');
    const generateButton = document.getElementById('generateButton');
    const questionsSection = document.getElementById('questionsSection');
    const questionsContent = document.getElementById('questionsContent');

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
        fetch('/process_clause', {
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