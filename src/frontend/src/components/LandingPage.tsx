// src/frontend/src/components/LandingPage.tsx

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Container,
  Typography,
  Box
} from '@mui/material';

const LandingPage = () => {
  const [open, setOpen] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [projectPurpose, setProjectPurpose] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleCreateProject = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: projectName, purpose: projectPurpose }),
      });
      const data = await response.json();
      if (response.ok) {
        navigate(`/projects/${data.project_id}`);
      } else {
        alert("Error creating project: " + data.detail);
      }
    } catch (error) {
      alert("Error: " + error);
    } finally {
      setLoading(false);
      setOpen(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 8 }}>
        <Typography variant="h4" gutterBottom>
          Welcome
        </Typography>
        <Button variant="contained" onClick={() => setOpen(true)}>
          Create New Project
        </Button>
      </Box>
      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>Create New Project</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Project Name"
            type="text"
            fullWidth
            variant="outlined"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
          />
          <TextField
            margin="dense"
            label="Project Purpose"
            type="text"
            fullWidth
            variant="outlined"
            value={projectPurpose}
            onChange={(e) => setProjectPurpose(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleCreateProject} variant="contained" disabled={loading}>
            {loading ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default LandingPage;
