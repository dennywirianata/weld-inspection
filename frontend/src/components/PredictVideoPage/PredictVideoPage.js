// src/components/PredictVideoPage/PredictVideoPage.js
import React, { useState } from 'react';
import axios from 'axios';
import { Form, Button, Alert, ProgressBar } from 'react-bootstrap';
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css'; // Import rc-slider CSS
import { FaCheckCircle, FaTimesCircle } from 'react-icons/fa';
import './PredictVideoPage.css';

const PredictVideoPage = ({ onResult }) => {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState('');
  const [confidence, setConfidence] = useState('');
  const [error, setError] = useState('');
  const [videoUrl, setVideoUrl] = useState('');
  const [totalFrames, setTotalFrames] = useState(0);
  const [acceptableFrames, setAcceptableFrames] = useState(0);
  const [rejectableFrames, setRejectableFrames] = useState(0);
  const [acceptablePercentage, setAcceptablePercentage] = useState(0);
  const [rejectablePercentage, setRejectablePercentage] = useState(0);
  const [framePredictions, setFramePredictions] = useState([]);
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
  const [currentFrameUrl, setCurrentFrameUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false); // Loading state
  const [processedVideoUrl, setProcessedVideoUrl] = useState(''); // Processed video URL

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError('');
    // Create a URL for the video preview
    if (e.target.files[0]) {
      setVideoUrl(URL.createObjectURL(e.target.files[0]));
    } else {
      setVideoUrl('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file.');
      return;
    }
    setError('');
    setIsLoading(true); // Show loading spinner
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${process.env.REACT_APP_API_URL}/upload/video`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      //setResult(response.data.status);
      //setConfidence(response.data.details);
      setVideoUrl(response.data.video_url);
      setTotalFrames(response.data.total_frames);
      setAcceptableFrames(response.data.acceptable_frames);
      setRejectableFrames(response.data.rejectable_frames);
      setAcceptablePercentage(response.data.acceptable_percentage);
      setRejectablePercentage(response.data.rejectable_percentage);
      setFramePredictions(response.data.frame_predictions);
      setProcessedVideoUrl(response.data.processed_video_url);
      onResult(response.data);
    } catch (error) {
      console.error('Error uploading file:', error);
      setResult('Error processing file');
      setConfidence('');
      setVideoUrl('');
      setTotalFrames(0);
      setAcceptableFrames(0);
      setRejectableFrames(0);
      setAcceptablePercentage(0);
      setRejectablePercentage(0);
      setFramePredictions([]);
      setCurrentFrameIndex(0);
      setCurrentFrameUrl('');
      setError('Error processing file');
    } finally {
      setIsLoading(false); // Hide loading spinner
    }
  };

  const handleSliderChange = (value) => {
    setCurrentFrameIndex(value);
    const framePrediction = framePredictions.find(fp => fp.index === value);
    if (framePrediction) {
      const frameImageUrl = `${process.env.REACT_APP_API_URL}/uploads/frame_${value}.jpg`;
      setCurrentFrameUrl(frameImageUrl);
      //setCurrentFrameUrl(framePrediction.frame_url); // Use the Firebase URL directly
    }
  };

  const renderProgressBars = () => {
    if (framePredictions.length === 0) return null;

    // Sort frame predictions by index
    const sortedFramePredictions = [...framePredictions].sort((a, b) => a.index - b.index);

    // Create progress bar segments
    const segments = [];
    let currentStart = 0;
    let currentType = sortedFramePredictions[0].status;

    for (let i = 0; i < sortedFramePredictions.length; i++) {
      const prediction = sortedFramePredictions[i];
      if (prediction.status !== currentType || i === sortedFramePredictions.length - 1) {
        const length = i - currentStart + 1;
        segments.push({
          start: currentStart,
          length: length,
          type: currentType
        });
        currentStart = i + 1;
        currentType = prediction.status;
      }
    }

    return segments.map(segment => (
      <div
        key={segment.start}
        className={`progress-bar-segment ${segment.type.toLowerCase()}`}
        style={{
          left: `${(segment.start / totalFrames) * 100}%`,
          width: `${(segment.length / totalFrames) * 100}%`,
        }}
      ></div>
    ));
  };

  const handleDownload = () => {
    if (processedVideoUrl) {
      const link = document.createElement('a');
      link.href = processedVideoUrl;
      link.setAttribute('download', 'processed_video.mp4'); // Set the file name
      document.body.appendChild(link);
      link.click();
      link.remove();
    }
  };

  return (
    <div className="predict-video-page">
      <h2>Predict Video</h2>
      <Form onSubmit={handleSubmit}>
        <Form.Group controlId="formFile">
          <Form.Label>Select a video:</Form.Label>
          <Form.Control type="file" accept="video/*" onChange={handleFileChange} />
        </Form.Group>
        <Button variant="primary" type="submit" className="mt-3">
          {isLoading ? 'Uploading...' : 'Inspect'}
        </Button>
      </Form>

      {isLoading && (
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
      )}

      {error && <Alert variant="danger" className="mt-3">{error}</Alert>}
      {videoUrl && (
        <div className="mt-4">
          
          
          <div className="frame-preview mt-3">
            <h4>Video Preview:</h4>
            {currentFrameUrl && (
              <img src={currentFrameUrl} alt="Frame" className="small-image" />
            )}
            <Slider
              min={0}
              max={totalFrames - 1}
              value={currentFrameIndex}
              onChange={handleSliderChange}
              trackStyle={[{ backgroundColor: '#007bff' }, { backgroundColor: '#dc3545' }]}
              railStyle={{ backgroundColor: '#e9ecef' }}
              handleStyle={{
                borderColor: '#007bff',
                borderWidth: 2,
                height: 15,
                width: 15,
                marginLeft: 0,
                marginTop: -5,
                backgroundColor: '#fff',
              }}
            />
          </div>
          <div className="progress-bar-container">
            <ProgressBar>
              {renderProgressBars()}
            </ProgressBar>
            
          </div>
          <div className="legend">
              <span className="legend-item"><span className="color-box green"></span> Accepted</span>
              <span className="legend-item"><span className="color-box red"></span> Rejected</span>
          </div>
        </div>
      )}
        
        {processedVideoUrl && (
          <Button variant="success" onClick={handleDownload} className="mt-3">
            Download Processed Video
          </Button>
        )}
    </div>
  );
};

export default PredictVideoPage;