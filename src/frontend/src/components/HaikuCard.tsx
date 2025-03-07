import React, { useState } from 'react';
import { Card, CardHeader, CardContent, Typography, IconButton, Dialog, DialogTitle, DialogContent, TextField, DialogActions, Button } from '@mui/material';
import WebStoriesIcon from '@mui/icons-material/WebStories';

interface HaikuCardProps {
  haiku: any;
}

const HaikuCard: React.FC<HaikuCardProps> = ({ haiku }) => {
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

  const [directions, setDirections] = useState("");
  const [loading, setLoading] = useState(false);

  const generateImagePrompts = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/projects/get-image-prompts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          haiku_id: haikuObj.id,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        alert("generateImagePrompts error: " + (data));
      } else {
        console.log("generateImagePrompts output:", data);
      }
    } catch (error) {
      alert("generateImagePrompts error: " + error);
    } finally {
      setLoading(false);
      setDirections("");
    }
  };

  

  return (
    <div style={{ position: 'relative', marginBottom: '2rem' }}>
      <Card>
        <CardHeader
          title={haikuObj.title || "Untitled Haiku"}
          action={
            <IconButton onClick={() => generateImagePrompts()}>
              <WebStoriesIcon color="primary" />
            </IconButton>
          }
        />
        <CardContent>
          <Typography variant="body1">
            {haikuObj.text}
          </Typography>
        </CardContent>
      </Card>

    </div>
  );
};

export default HaikuCard;
