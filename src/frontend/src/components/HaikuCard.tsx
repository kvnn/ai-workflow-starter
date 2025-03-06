import React, { useState } from 'react';
import { Card, CardHeader, CardContent, Typography, IconButton, Dialog, DialogTitle, DialogContent, TextField, DialogActions, Button } from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings';
import HaikuDetailsCard from './HaikuDetailsCard';

interface HaikuCardProps {
  haiku: any;
  projectId: string;
  details: any[];
}

const HaikuCard: React.FC<HaikuCardProps> = ({ haiku, projectId, details }) => {
  let haikuObj: any = {};
  if (typeof haiku === 'string') {
    try {
      haikuObj = JSON.parse(haiku);
    } catch (e) {
      haikuObj = { text: haiku };
    }
  } else if (typeof haiku === 'object' && haiku !== null) {
    haikuObj = haiku;
  }

  const [inferenceDialogOpen, setInferenceDialogOpen] = useState(false);
  const [directions, setDirections] = useState("");
  const [loading, setLoading] = useState(false);

  const handleInfer = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/projects/infer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: parseInt(projectId),
          haiku: haikuObj,
          directions: directions,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        alert("Error during inference: " + (data.detail || data.error));
      } else {
        console.log("Inference output:", data);
      }
    } catch (error) {
      alert("Error during inference: " + error);
    } finally {
      setLoading(false);
      setInferenceDialogOpen(false);
      setDirections("");
    }
  };

  return (
    <div style={{ position: 'relative', marginBottom: '2rem' }}>
      <Card>
        <CardHeader
          title={haikuObj.title || "Untitled Haiku"}
          action={
            <IconButton onClick={() => setInferenceDialogOpen(true)}>
              <SettingsIcon color="primary" />
            </IconButton>
          }
        />
        <CardContent>
          <Typography variant="body1">
            {haikuObj.haiku}
          </Typography>
        </CardContent>
      </Card>

      {details && details.map((detail, index) => (
        <HaikuDetailsCard key={detail.id} details={detail} offset={index * 50} />
      ))}


      <Dialog open={inferenceDialogOpen} onClose={() => setInferenceDialogOpen(false)}>
        <DialogTitle>Enter Directions for Inference</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Directions"
            type="text"
            fullWidth
            variant="outlined"
            value={directions}
            onChange={(e) => setDirections(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInferenceDialogOpen(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleInfer} variant="contained" disabled={loading}>
            {loading ? 'Processing...' : 'Submit'}
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default HaikuCard;
