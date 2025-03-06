import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.js";

import { RecoilRoot } from "recoil";


import { BrowserRouter, Routes, Route } from 'react-router-dom';
import "./style.css";


ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>

      <RecoilRoot>
        <BrowserRouter>
          <Routes>
            <Route
              path="/*"
              element={
                  <App />
              }
            />

          </Routes>
        </BrowserRouter>
      </RecoilRoot>
  </React.StrictMode>
);
