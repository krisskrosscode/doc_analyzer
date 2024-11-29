from flask import Flask, request, render_template, jsonify, session
import requests
import os
import pypdf

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

def generate_response(prompt, conversation_history, file_content):
    formatted_history = "\n".join(conversation_history)
    
    full_prompt = f"File content:\n{file_content}\n\nConversation history:\n{formatted_history}\n\nHuman: {prompt}\nAI:"
    url = 'http://localhost:11434/v1/completions'
    headers = {'Content-Type': 'application/json'}
    data = {
        'prompt': full_prompt,
        'model': 'zysec:latest',
        'max_tokens': 5000  # Adjust as needed
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['choices'][0]['text']
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {e}"

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'md', 'py', 'js', 'html', 'css', 'json', 'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/inspection_assist')
def generate_questions():
    ai_response = ""
    clauses = ["Recovery  plans  shall be updated  and  improved  to  incorporate  lessons learned from cybersecurity incidents", 
               "REs  shall  formulate strategies  to  anticipate  new  attack  vectors  by removing   or   applying   new   controls to   compensate   for   identified vulnerabilities or weaknesses, reducing or manipulating attack surfaces, and   proactively   orienting   controls,   practices,   and   capabilities   to prospective, emerging, or potential threats.", 
               "Cybersecurity  incidents shall  be categorized in-line with categorization given in RE’s CCMP"]  # Example clause list
    ai_response = process_clause()
    return render_template('inspection_assist.html', clauses=clauses, ai_response=ai_response)

@app.route('/process_clause', methods=['POST'])
def process_clause():

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    selected_clause = data.get('clause')
    
    if not selected_clause:
        return jsonify({'error': 'No clause selected'}), 400

    # Prepare prompt for the LLM
    # prompt = f"You are a regulatory compliance expert carrying out inspection of one of your regulated entities (RE). The REs have to comply to clauses mandated by you. Please generate 5 questions that you can ask the RE to check the compliance with this clause: \n\n{selected_clause}. Also provide detailed steps to check the compliance by asking their teams to show their systems and documents and see what to check."
    prompt = f"You are a National Stock Market Regulator. You have been given a task to inspect an entity regulated by you by going on site. Here is a clause from a cybersecurity circular published by you. It is to complied by the entity regulated by you. Please generate 5 questions that you can ask the entity to check the compliance with this clause: \n\n{selected_clause}. Also provide detailed steps to check the compliance by asking their teams to show their systems and documents and see what to check."
    try:
       
        response = requests.post('http://localhost:11434/api/generate',
                               json={
                                   "model": "zysec:latest", 
                                   "prompt": prompt,
                                   "stream": False
                               })
       
        if response.status_code == 200:
            llm_response = response.json()['response']
        
            return jsonify({'response': llm_response})
        else:
            return jsonify({'error': 'Failed to get response from LLM server'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/audit_report_analysis')
def audit_report_analysis():
    ai_response = ""
    clauses = ["Recovery  plans  shall be updated  and  improved  to  incorporate  lessons learned from cybersecurity incidents", 
               "REs  shall  formulate strategies  to  anticipate  new  attack  vectors  by removing   or   applying   new   controls to   compensate   for   identified vulnerabilities or weaknesses, reducing or manipulating attack surfaces, and   proactively   orienting   controls,   practices,   and   capabilities   to prospective, emerging, or potential threats.", 
               "Cybersecurity  incidents shall  be categorized in-line with categorization given in RE’s CCMP"]  # Example clause list
    ai_response = report_rag()
    return render_template('audit_report_analysis.html', clauses=clauses, ai_response=ai_response)

@app.route('/report_rag', methods=['POST'])
def report_rag():

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    selected_clause = data.get('clause')
    
    if not selected_clause:
        return jsonify({'error': 'No clause selected'}), 400

    file_content = session.get('file_content', '')
    # Prepare prompt for the LLM
    # prompt = f"You are a regulatory compliance expert carrying out cybersecurity inspection of one of your regulated entities (RE). The REs have to comply to clauses mandated by you. Please generate 5 questions that you can ask the RE to check the compliance with this clause: \n\n{selected_clause}. Also provide detailed steps to check the compliance by asking their teams to show their systems and documents and see what to check."
    prompt = f"You are a National Stock Market Regulator. You have been given a task to check cybersecurity compliance an entity regulated by you by going on site. Here is a clause from a cybersecurity circular published by you.  \n\n{selected_clause}. Check if the compliace of the clause is being checked in the cybersecurity audit report uploaded as {file_content}. Strictly give your comments only when relevant details i.e. compliance with report to the clause written in {selected_clause} are found in the {file_content}, Otherwise return result saying the details are not covered in the report"
    try:
       
        response = requests.post('http://localhost:11434/api/generate',
                               json={
                                   "model": "zysec:latest", 
                                   "prompt": prompt,
                                   "stream": False
                               })
       
        if response.status_code == 200:
            llm_response = response.json()['response']
        
            return jsonify({'response': llm_response})
        else:
            return jsonify({'error': 'Failed to get response from LLM server'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file and allowed_file(file.filename):
        try:
            if file.filename.lower().endswith('.pdf'):
                pdf_reader = pypdf.PdfReader(file)
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text()
            else:
                content = file.read().decode('utf-8')
            
            action = request.form.get('action', 'upload')
            
            if action == 'clear':
                session['conversation_history'] = []
            elif action == 'keep':
                # Keep the existing conversation history
                if 'conversation_history' in session and session['conversation_history']:
                    session['conversation_history'].append("System: New file uploaded. Previous context may or may not apply.")
            else:
                # Default action (upload without existing chat)
                session['conversation_history'] = []
            
            session['file_content'] = content
            return jsonify({
                'content': content,
                'chatHistory': session.get('conversation_history', [])
            })
        except Exception as e:
            return jsonify({'error': f'Error reading file: {str(e)}'})
    else:
        return jsonify({'error': 'File type not allowed'})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data['message']
    conversation_history = session.get('conversation_history', [])
    file_content = session.get('file_content', '')

    # Add user input to conversation history
    conversation_history.append(f"Human: {user_input}")

    # Generate AI response
    ai_response = generate_response(user_input, conversation_history, file_content)

    # Add AI response to conversation history
    conversation_history.append(f"AI: {ai_response}")

    # Store updated history in session
    session['conversation_history'] = conversation_history

    return jsonify({
        'response': ai_response,
        'full_history': conversation_history
    })

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    session['conversation_history'] = []
    return jsonify({'status': 'success', 'message': 'Chat history cleared'})

@app.route('/clear_all', methods=['POST'])
def clear_all():
    session.clear()
    return jsonify({'status': 'success', 'message': 'All data cleared'})

if __name__ == "__main__":
    app.run(debug=True)