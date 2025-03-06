import { Routes, Route } from 'react-router-dom';

import LandingPage from './components/LandingPage';
import { useContext, useEffect } from 'react';


function App() { 
  return (
    <>
      <Routes>
        <Route path="/" element={<LandingPage />} />
      </Routes>
    </>
  );
}

export default App;
