import React, { useState } from "react";
import {
  Card, CardHeader, CardContent, Typography, IconButton,
  Dialog, DialogTitle, DialogContent, TextField, DialogActions, Button, Box, CardMedia
} from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import WebStoriesIcon from "@mui/icons-material/WebStories";
import ImageIcon from "@mui/icons-material/Image";
import ZoomInIcon from "@mui/icons-material/ZoomIn"; // Icon for viewing full image

interface HaikuCardProps {
  haiku: any;
}

const HaikuCard: React.FC<HaikuCardProps> = ({ haiku }) => {
  const [loading, setLoading] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [imageModalOpen, setImageModalOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState("");
  const [editingPrompt, setEditingPrompt] = useState({ id: "", text: "" });

  const generateImage = async (promptId: string) => {
    setLoading(true);
    try {
      await fetch("http://localhost:8000/projects/generate-image", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt_id: promptId, haiku_id: haiku.id }),
      });
    } catch (error) {
      console.error("Error generating image:", error);
    } finally {
      setLoading(false);
    }
  };

  const openEditModal = (prompt) => {
    setEditingPrompt(prompt);
    setEditModalOpen(true);
  };

  const handleSaveEdit = async () => {
    try {
      await fetch("http://localhost:8000/projects/update-image-prompt", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt_id: editingPrompt.id,
          new_text: editingPrompt.text,
        }),
      });
      setEditModalOpen(false);
    } catch (error) {
      console.error("Error updating image prompt:", error);
    }
  };

  const openImageModal = (b64Image: string) => {
    setSelectedImage(`data:image/png;base64,${b64Image}`);
    setImageModalOpen(true);
  };

  return (
    <Card sx={{ mb: 4 }}>
      <CardHeader
        title={haiku.title || "Untitled Haiku"}
        action={
          <IconButton onClick={() => generateImage(haiku.id)} disabled={loading}>
            <WebStoriesIcon color="primary" />
          </IconButton>
        }
      />
      <CardContent>
        <Typography 
            variant="body1"
        >{haiku.text}</Typography>

        {/* Image Prompts Section */}
        {haiku.image_prompts && haiku.image_prompts.length > 0 && (
          <Box sx={{ mt: 2, display: "flex", gap: 2, flexWrap: "wrap", overflowX: "auto" }}>
            {haiku.image_prompts.map((prompt) => (
              <Card key={prompt.id} sx={{ p: 2, minWidth: 250, position: "relative" }}>
                <IconButton
                  size="small"
                  sx={{ position: "absolute", top: 4, right: 4 }}
                  onClick={() => openEditModal(prompt)}
                >
                  <EditIcon fontSize="small" />
                </IconButton>

                <Typography sx={{ mb: 2}} variant="body2">{prompt.text}</Typography>

                {/* "Generate Image" Button */}
                <IconButton
                  size="small"
                  sx={{ position: "absolute", bottom: 4, left: 4 }}
                  onClick={() => generateImage(prompt.id)}
                >
                  <ImageIcon fontSize="small" />
                </IconButton>

                {/* Image Thumbnails */}
                {prompt.images && prompt.images.length > 0 && (
                  <Box sx={{ mt: 2, mb: 4, display: "flex", gap: 1 }}>
                    {prompt.images.map((img) => (
                      <CardMedia
                        key={img.id}
                        component="img"
                        image={`data:image/png;base64,${img.b64}`}
                        alt="Generated"
                        sx={{
                          borderRadius: 1,
                          border: "1px solid #ccc",
                          height: 80,
                          width: 80,
                          cursor: "pointer",
                        }}
                        onClick={() => openImageModal(img.b64)}
                      />
                    ))}
                  </Box>
                )}
              </Card>
            ))}
          </Box>
        )}
      </CardContent>

      {/* Edit Image Prompt Modal */}
      <Dialog open={editModalOpen} onClose={() => setEditModalOpen(false)}>
        <DialogTitle>Edit Image Prompt</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            minRows={3}
            value={editingPrompt.text}
            onChange={(e) => setEditingPrompt({ ...editingPrompt, text: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditModalOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveEdit} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      {/* Image Fullscreen Modal */}
      <Dialog open={imageModalOpen} onClose={() => setImageModalOpen(false)} maxWidth="lg" fullWidth>
        <DialogContent sx={{ display: "flex", justifyContent: "center", alignItems: "center", p: 2 }}>
          {selectedImage && (
            <a href={selectedImage} target="_blank" rel="noopener noreferrer">
              <img
                src={selectedImage}
                alt="Generated"
                style={{
                  maxWidth: "95%",
                  maxHeight: "95vh",
                  objectFit: "contain",
                  cursor: "pointer",
                }}
              />
            </a>
          )}
        </DialogContent>
      </Dialog>
    </Card>
  );
};

export default HaikuCard;
