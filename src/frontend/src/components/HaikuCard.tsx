// src/frontend/src/components/HaikuCard.tsx

import React from 'react';
import { Card, CardHeader, CardContent, Typography } from '@mui/material';

interface HaikuCardProps {
  haiku: any;
}

const HaikuCard: React.FC<HaikuCardProps> = ({ haiku }) => {
  // Ensure haiku is an object.
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

  // You can now use haikuObj.title, haikuObj.text, etc.
  return (
    <Card sx={{ mt: 2 }}>
      {haikuObj.title && <CardHeader title={haikuObj.title} />}
      <CardContent>
        <Typography variant="body1">
          {haikuObj.haiku}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default HaikuCard;
