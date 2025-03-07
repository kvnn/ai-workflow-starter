import React, { useState } from "react";
import { Card, CardHeader, CardContent, Typography, IconButton } from "@mui/material";
import WebStoriesIcon from "@mui/icons-material/WebStories";
import HaikuDetailsCard from "./HaikuDetailsCard";

interface HaikuCardProps {
  haiku: any;
}

const HaikuCard: React.FC<HaikuCardProps> = ({ haiku }) => {
  const [loading, setLoading] = useState(false);

  const generateImagePrompts = async () => {
    setLoading(true);
    try {
      await fetch("http://localhost:8000/projects/get-image-prompts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ haiku_id: haiku.id }),
      });
    } catch (error) {
      console.error("generateImagePrompts error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ position: "relative", marginBottom: "2rem" }}>
      <Card>
        <CardHeader
          title={haiku.title || "Untitled Haiku"}
          action={
            <IconButton onClick={generateImagePrompts} disabled={loading}>
              <WebStoriesIcon color="primary" />
            </IconButton>
          }
        />
        <CardContent>
          <Typography variant="body1">{haiku.text}</Typography>
        </CardContent>
      </Card>

      {haiku.image_prompts &&
        haiku.image_prompts.map((prompt, index) => (
          <HaikuDetailsCard key={prompt.id} details={prompt.text} offset={index * 50} />
        ))}
    </div>
  );
};

export default HaikuCard;
