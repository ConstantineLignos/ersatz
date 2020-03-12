import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from collections import namedtuple
import random
import os
     
class TransformerModel(nn.Module):
    
    def __init__(self, vocab, left_context_size, right_context_size, embed_size=512, nhead=8, num_layers=2):
        super(TransformerModel, self).__init__()

        # each layer of the transformer
        encoder_layer = nn.TransformerEncoderLayer(embed_size, nhead)
        # build the transformer with n of the previous layers
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # embeds the input into a embed_size dimensional space
        self.src_emb = nn.Embedding(len(vocab), embed_size)
        # uses sine function to get positional embeddings
        self.pos_embed = PositionalEncoding(embed_size=embed_size, max_len=(left_context_size + right_context_size+1))

        # vocab; includes stoi and itos look ups
        self.vocab = vocab
        self.embed_size = embed_size
        self.left_context_size = left_context_size
        self.right_context_size = right_context_size        
        self.max_size = self.left_context_size + self.right_context_size + 1

        # takes flattened output of last layer and maps to vocabulary size
        print(f'vocab size: {len(self.vocab)}')
        print(f'embed_size: {self.embed_size}')
        print(f'max_size: {self.max_size}')
        self.generator = Generator(self.embed_size*self.max_size, len(self.vocab))

    def forward(self, src):
        src = src.t()
        embed = self.pos_embed(self.src_emb(src) * math.sqrt(self.embed_size))
        output = self.encoder(embed).transpose(0,1)
        output = output.reshape(output.size()[0], -1)
        return self.generator(output)

    def predict_word(self, src):
        output = self.forward(src)
        return self.vocab.itos[torch.argmax(output)]

class Generator(nn.Module):
    
    # could change this to mean-pool or max pool
    def __init__(self, embed_size, vocab_size):
        super(Generator, self).__init__()
        self.proj = nn.Linear(embed_size, vocab_size)
    
    def forward(self, x):
        return F.log_softmax(self.proj(x), dim=-1)


class PositionalEncoding(nn.Module):
    
    def __init__(self, embed_size=512, dropout=0.1, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(dropout)
        pe = torch.zeros(max_len, embed_size)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, embed_size, 2).float() * (-math.log(10000.0) / embed_size))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0,1)
        self.register_buffer('pe', pe)
        
    def forward(self, x):
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)
    

