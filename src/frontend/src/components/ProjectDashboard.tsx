// src/frontend/src/components/ProjectDashboard.tsx

import React, { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Container, Typography, Box } from '@mui/material';
import ReconnectingWebSocket from 'reconnecting-websocket';

const ProjectDashboard = () => {
  const { id } = useParams();

  useEffect(() => {
    if (!id) return;
    const wsUrl = `ws://localhost:8000/projects/dashboard/${id}`;
    const rws = new ReconnectingWebSocket(wsUrl);

    rws.addEventListener('open', () => {
      console.log(`ReconnectingWebSocket connected for project: ${id}`);
    });

    rws.addEventListener('message', (event) => {
      console.log("Received data:", event.data);
    });

    rws.addEventListener('error', (error) => {
      console.error("ReconnectingWebSocket error:", error);
    });

    rws.addEventListener('close', () => {
      console.log("ReconnectingWebSocket connection closed.");
    });

    return () => {
      rws.close();
    };
  }, [id]);

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" gutterBottom>
          Project Dashboard
        </Typography>
        <Typography variant="subtitle1">
          Viewing project with ID: {id}
        </Typography>
      </Box>
    </Container>
  );
};

export default ProjectDashboard;
