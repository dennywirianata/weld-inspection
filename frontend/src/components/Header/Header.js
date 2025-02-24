// plop-templates\component.hbs
import React, { useState } from 'react';
import axios from 'axios';
import { Form, Button, Alert } from 'react-bootstrap';
import './Header.css';

const Header = () => {
  return (
      <header className="header">
          <div className="logo">
              <img src="/welding-logo.png" alt="Welding Logo" />
              <h1>AI Weld Inspector</h1>
          </div>
          <p>Revolutionizing weld inspection with AI</p>
      </header>
  );
};

export default Header;