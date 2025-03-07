import React, { useState } from "react";
import {
  Card, CardHeader, CardContent, Typography, IconButton,
  Dialog, DialogTitle, DialogContent, TextField, DialogActions, Button, Box
} from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import WebStoriesIcon from "@mui/icons-material/WebStories";

interface HaikuCardProps {
  haiku: any;
}

const HaikuCard: React.FC<HaikuCardProps> = ({ haiku }) => {
  const [loading, setLoading] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState({ id: "", text: "" });

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

  return (
    <Card sx={{ mb: 4 }}>
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
                <Typography variant="body2">{prompt.text}</Typography>
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
    </Card>
  );
};

export default HaikuCard;
