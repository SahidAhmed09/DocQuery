import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleFileUpload = async (event) => {
    event.preventDefault();
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://127.0.0.1:8000/api/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      alert(response.data.message);
    } catch (error) {
      alert('Error uploading file');
    }
  };

  const handleQuerySubmit = async (event) => {
    event.preventDefault();

    try {
      const response = await axios.post('http://127.0.0.1:8000/api/query/', { query });
      setMessages([...messages, { text: query, type: 'user' }, { text: response.data.response, type: 'bot' }]);
      setQuery('');
    } catch (error) {
      alert('Error querying the PDF');
    }
  };

  return (
    <div className="app-container">
      <div className="chat-container">
        <div className="chat-header">
          <h1>DocQuery</h1>
        </div>
        <div className="chat-box">
          {messages.map((message, index) => (
            <div key={index} className={`chat-message ${message.type}`}>
              {message.text}
            </div>
          ))}
        </div>
        <div className="chat-input">
          <form onSubmit={handleFileUpload}>
            <input type="file" onChange={handleFileChange} accept=".pdf" required />
            <button type="submit">Upload PDF</button>
          </form>
          <form onSubmit={handleQuerySubmit}>
            <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Ask a question about the PDF" required />
            <button type="submit">Send</button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;
