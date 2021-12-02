import tensorflow as tf
import torch
import torch.nn.functional as F
from torch_geometric.nn import GATConv


class ST_GAT(torch.nn.Module):

    def __init__(self, in_channels, out_channels, num_nodes, heads=8, dropout=0.6):
        super(ST_GAT, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.heads = heads
        self.dropout = dropout
        self.num_nodes = num_nodes

        # single graph attentional layer with 8 attention heads
        self.gat = GATConv(in_channels=self.in_channels, out_channels= self.in_channels,
            heads=heads, dropout=self.dropout, concat=False)

        # add two LSTM layers
        self.lstm1 = torch.nn.LSTM(input_size=self.num_nodes, hidden_size=32, num_layers=1)
        self.lstm2 = torch.nn.LSTM(input_size=32, hidden_size=128, num_layers=1)

        # fully-connected neural network
        self.linear = torch.nn.Linear(128, self.out_channels)

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        # apply dropout
        x = torch.FloatTensor(x)
        # gat layer
        x = self.gat(x, edge_index)
        x = F.dropout(x, self.dropout, training=self.training)
        x = F.log_softmax(x, dim=1)

        # RNN: 2 LSTM
        # incoming: x is (batchsize*num_nodes, seq_length), change into (batch_size, num_nodes, seq_length)
        x = torch.reshape(x, (data.num_graphs, int(data.num_nodes/data.num_graphs), data.num_features)) #TODO: should this be batch then nodes or nodes then batch?
        # for lstm: x should be (seq_length, batch_size, input_dim)
        # sequence length = 12, batch_size = 50, input_dim = 228
        #TODO move the dimensions around! below line is not correct
        x = torch.unsqueeze(torch.transpose(x, 0, 1), dim=1)
        x, _ = self.lstm1(x)
        x, _ = self.lstm2(x)

        # final output layer
        x = self.linear(x)

        return x

# class LSTM1(nn.Module):
#     def __init__(self, num_classes, input_size, hidden_size, num_layers, seq_length):
#         super(LSTM1, self).__init__()
#         self.num_classes = num_classes #number of classes
#         self.num_layers = num_layers #number of layers
#         self.input_size = input_size #input size
#         self.hidden_size = hidden_size #hidden state
#         self.seq_length = seq_length #sequence length

#         self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size,
#                           num_layers=num_layers, batch_first=True) #lstm
#         self.fc_1 =  nn.Linear(hidden_size, 128) #fully connected 1
#         self.fc = nn.Linear(128, num_classes) #fully connected last layer

#         self.relu = nn.ReLU()

#     def forward(self,x):
#         h_0 = Variable(torch.zeros(self.num_layers, x.size(0), self.hidden_size)) #hidden state
#         c_0 = Variable(torch.zeros(self.num_layers, x.size(0), self.hidden_size)) #internal state
#         # Propagate input through LSTM
#         output, (hn, cn) = self.lstm(x, (h_0, c_0)) #lstm with input, hidden, and internal state
#         hn = hn.view(-1, self.hidden_size) #reshaping the data for Dense layer next
#         out = self.relu(hn)
#         out = self.fc_1(out) #first Dense
#         out = self.relu(out) #relu
#         out = self.fc(out) #Final Output
#         return out