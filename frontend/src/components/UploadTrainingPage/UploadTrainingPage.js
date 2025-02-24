// src/components/UploadTrainingPage/UploadTrainingPage.js
import React, { useState } from 'react';
import axios from 'axios';
import { Form, Button, Alert } from 'react-bootstrap';
import './UploadTrainingPage.css';

const UploadTrainingPage = ({ onTrainingStatus }) => {
  const [trainingFile, setTrainingFile] = useState(null);
  const [trainingStatus, setTrainingStatus] = useState('');
  const [trainingError, setTrainingError] = useState('');

  const handleTrainingFileChange = (e) => {
    setTrainingFile(e.target.files[0]);
    setTrainingError('');
  };

  const handleTrainingSubmit = async (e) => {
    e.preventDefault();
    if (!trainingFile) {
      setTrainingError('Please select a file.');
      return;
    }

    const formData = new FormData();
    formData.append('file', trainingFile);

    try {
      const response = await axios.post(`${process.env.REACT_APP_API_URL}/train`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setTrainingStatus(response.data.message);
      onTrainingStatus(response.data.message);
    } catch (error) {
      console.error('Error uploading training file:', error);
      setTrainingStatus('Error uploading training file');
      setTrainingError('Error uploading training file');
    }
  };

  return (
    <div className="upload-training-page">
      <h2>Upload Training Data</h2>
      <Form onSubmit={handleTrainingSubmit}>
        <Form.Group controlId="formTrainingFile">
          <Form.Label>Select an image for training:</Form.Label>
          <Form.Control type="file" accept="image/*" onChange={handleTrainingFileChange} />
        </Form.Group>
        <Button variant="primary" type="submit" className="mt-3">
          Upload for Training
        </Button>
      </Form>

      {trainingError && <Alert variant="danger" className="mt-3">{trainingError}</Alert>}
      {trainingStatus && <Alert variant="success" className="mt-3">{trainingStatus}</Alert>}
    </div>
  );
};

export default UploadTrainingPage;