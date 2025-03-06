import React from 'react';
import Draggable from 'react-draggable';
import { Card, CardContent, Typography } from '@mui/material';

interface HaikuDetailsCardProps {
  details: any;
  offset: number;
}

const HaikuDetailsCard: React.FC<HaikuDetailsCardProps> = ({ details, offset }) => {
  return (
    <Draggable>
      <Card
        variant="outlined"
        sx={{
          width: 200,
          position: 'absolute',
          top: offset,
          right: 0,
          cursor: 'move',
          m: 1,
          backgroundColor: '#f0f0f0',
        }}
      >
        <CardContent>
          <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', fontSize: '0.75rem' }}>
            {JSON.stringify(details, null, 2)}
          </Typography>
        </CardContent>
      </Card>
    </Draggable>
  );
};

export default HaikuDetailsCard;
