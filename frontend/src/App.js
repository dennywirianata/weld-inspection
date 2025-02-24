import React, { useState } from 'react';
import { Tabs, Tab } from 'react-bootstrap';
import Header from './components/Header';
import PredictImagePage from './components/PredictImagePage';
import PredictVideoPage from './components/PredictVideoPage';
import UploadTrainingPage from './components/UploadTrainingPage';
import Footer from './components/Footer';
import Background from './components/Background';
import './styles/global.css';

function App() {
  const [inspectionResult, setInspectionResult] = useState('');
  const [inspectionConfidence, setInspectionConfidence] = useState('');
  const [trainingStatus, setTrainingStatus] = useState('');

  const handleImageResult = (data) => {
    setInspectionResult(data.status);
    setInspectionConfidence(data.details);
  };

  const handleTrainingStatus = (status) => {
    setTrainingStatus(status);
  };

  
  return (
    <div className="App">
        <Header />
      <Background />
       

      <Tabs defaultActiveKey="predict-image" id="uncontrolled-tab-example" className="mb-3">
        <Tab eventKey="predict-image" title="Predict Image">
          <PredictImagePage onResult={handleImageResult} />
        </Tab>
        <Tab eventKey="predict-video" title="Predict Video">
          <PredictVideoPage onResult={handleImageResult} />
        </Tab>
        <Tab eventKey="upload-training" title="Upload Training Data">
          <UploadTrainingPage onTrainingStatus={handleTrainingStatus} />
        </Tab>
      </Tabs>
      <Footer />
    </div>

  );
}

export default App;