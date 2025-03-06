import { Routes, Route } from 'react-router-dom';

import LandingPage from './components/LandingPage';
import ProjectDashboard from './components/ProjectDashboard';
import { useContext, useEffect } from 'react';


function App() { 
  return (
    <>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/projects/:id" element={<ProjectDashboard />} />
      </Routes>
    </>
  );
}

export default App;
