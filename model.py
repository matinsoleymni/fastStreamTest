import torch
from torch import nn

class TransformerClassification(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_heads, num_layers, output_dim=2):
        super(TransformerClassification, self).__init__()

        # You may need to transform input to match the hidden dimension if required
        self.fc_input = nn.Linear(input_dim, hidden_dim)  # If input dim does not match hidden_dim

        # Define the Transformer encoder (without embedding)
        self.encoder_layer = nn.TransformerEncoderLayer(d_model=hidden_dim, nhead=num_heads)
        self.transformer_encoder = nn.TransformerEncoder(self.encoder_layer, num_layers=num_layers)

        # Output layer
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        # Ensure input matches hidden_dim
        x = self.fc_input(x)  # This transforms input to hidden_dim size
        x = x.unsqueeze(1)  # Add sequence length dimension (seq_len=1)

        # Transformer encoding
        x = x.permute(1, 0, 2)  # Change to (seq_len, batch_size, hidden_dim)
        x = self.transformer_encoder(x)

        # Average pooling over the sequence length (since seq_len=1)
        x = x.mean(dim=0)  # (batch_size, hidden_dim)

        # Output layer
        x = self.fc(x)  # Final output layer for classification

        return x
