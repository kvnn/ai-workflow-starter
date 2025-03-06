// src/frontend/src/components/ProjectDashboard.tsx

import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  DialogActions,
} from '@mui/material';
import ReconnectingWebSocket from 'reconnecting-websocket';
import HaikuCard from './HaikuCard';

const ProjectDashboard = () => {
  const { id } = useParams();
  const [haikuModalOpen, setHaikuModalOpen] = useState(false);
  const [description, setDescription] = useState("");
  const [haikuLoading, setHaikuLoading] = useState(false);
  const [haikus, setHaikus] = useState<any[]>([]);

  useEffect(() => {
    if (!id) return;
    const wsUrl = `ws://localhost:8000/projects/dashboard/${id}`;
    const rws = new ReconnectingWebSocket(wsUrl);

    rws.addEventListener('open', () => {
      console.log(`WebSocket connected for project: ${id}`);
    });

    rws.addEventListener('message', (event) => {
      console.log("Received data:", event.data);
      try {
        const projectData = JSON.parse(event.data);
        if (projectData && projectData.haikus) {
          // reverse order of haikus
          const reversedHaikus = projectData.haikus.reverse();
          setHaikus(reversedHaikus);
        }
      } catch (err) {
        console.error("Error parsing project data:", err);
      }
    });

    rws.addEventListener('error', (error) => {
      console.error("WebSocket error:", error);
    });

    rws.addEventListener('close', () => {
      console.log("WebSocket connection closed.");
    });

    return () => {
      rws.close();
    };
  }, [id]);

  const handleHaikuSubmit = async () => {
    setHaikuLoading(true);
    try {
      const response = await fetch("http://localhost:8000/projects/haiku", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description, project_id: parseInt(id || "0") }),
      });
      const data = await response.json();
      if (!response.ok) {
        alert("Error creating haiku: " + (data.detail || data.error));
      } else {
        console.log("Haiku created:", data);
      }
    } catch (error) {
      alert("Error creating haiku: " + error);
    } finally {
      setHaikuLoading(false);
      setHaikuModalOpen(false);
      setDescription("");
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" gutterBottom>
          Project Dashboard
        </Typography>
        <Typography variant="subtitle1" gutterBottom>
          Viewing project with ID: {id}
        </Typography>
        <Button variant="contained" onClick={() => setHaikuModalOpen(true)}>
          Create Haiku
        </Button>
      </Box>

      <Dialog open={haikuModalOpen} onClose={() => setHaikuModalOpen(false)}>
        <DialogTitle>Create Haiku</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Description"
            type="text"
            fullWidth
            variant="outlined"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHaikuModalOpen(false)} disabled={haikuLoading}>
            Cancel
          </Button>
          <Button onClick={handleHaikuSubmit} variant="contained" disabled={haikuLoading}>
            {haikuLoading ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      <Box sx={{ mt: 4 }}>
        <Typography variant="h5">Haikus</Typography>
        {haikus.map((haiku, index) => (
          <HaikuCard key={index} haiku={haiku} />
        ))}
      </Box>
    </Container>
  );
};

export default ProjectDashboard;
