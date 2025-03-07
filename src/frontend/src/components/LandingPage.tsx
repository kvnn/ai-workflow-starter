import React, { useEffect, useState } from 'react';
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
  Box,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';

const LandingPage = () => {
  const [open, setOpen] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [loading, setLoading] = useState(false);
  const [projects, setProjects] = useState<any[]>([]); // Store projects
  const navigate = useNavigate();

  // Fetch list of projects from backend
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const response = await fetch('http://localhost:8000/projects');
        const data = await response.json();
        if (response.ok) {
          setProjects(data); // Ensure API response structure is correct
        } else {
          console.error("Error fetching projects:", data.detail);
        }
      } catch (error) {
        console.error("Error fetching projects:", error);
      }
    };

    fetchProjects();
  }, []);

  const handleCreateProject = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: projectName }),
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
        <Typography variant="h3" sx={{ mt: 4, mb: 2 }}>
          Projects
        </Typography>
        <Button variant="contained" onClick={() => setOpen(true)}>
          Create New Project
        </Button>
        <List>
          {projects.map((project) => (
            <ListItem 
              key={project.id} 
              button 
              onClick={() => navigate(`/projects/${project.id}`)}
            >
              <ListItemText primary={project.name} />
            </ListItem>
          ))}
        </List>
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
