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
  const [projectName, setProjectName] = useState('');
  const [haikus, setHaikus] = useState<any[]>([]);
  const [haikuModalOpen, setHaikuModalOpen] = useState(false);
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    const wsUrl = `ws://localhost:8000/projects/dashboard/${id}`;
    const rws = new ReconnectingWebSocket(wsUrl);

    rws.addEventListener('message', (event) => {
      console.log("Received data:", event.data);
      try {
        const projectData = JSON.parse(event.data);
        setProjectName(projectData.name);
        if (projectData && projectData.haikus) {
          setHaikus(projectData.haikus);
        }
      } catch (err) {
        console.error("Error parsing project data:", err);
      }
    });

    return () => {
      rws.close();
    };
  }, [id]);

  const handleHaikuSubmit = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/projects/haiku", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: parseInt(id || "0"),
          description: description,
        }),
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
      setLoading(false);
      setHaikuModalOpen(false);
      setDescription("");
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" gutterBottom>
          {projectName}
        </Typography>
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
          <Button onClick={() => setHaikuModalOpen(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleHaikuSubmit} variant="contained" disabled={loading}>
            {loading ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      <Box sx={{ mt: 4 }}>
        <Typography variant="h5">Haikus</Typography>
        <Button sx={{ mb: 4 }} variant="contained" onClick={() => setHaikuModalOpen(true)}>
          Create Haiku
        </Button>
        {haikus.map((haiku, index) => (
          <HaikuCard key={index} haiku={haiku} />
        ))}
      </Box>
    </Container>
  );
};

export default ProjectDashboard;
