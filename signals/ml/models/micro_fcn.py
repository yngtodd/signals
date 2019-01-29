import torch
from torch import nn
import torch.nn.functional as F


class DoubleBlock(nn.Module):
    '''(conv => BN => ReLU) * 2'''
    def __init__(self, in_ch, out_ch):
        super(DoubleBlock, self).__init__()

        self.conv = nn.Sequential(
            nn.Conv1d(in_ch, out_ch, 3, padding=1),
            nn.BatchNorm1d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv1d(out_ch, out_ch, 3, padding=1),
            nn.BatchNorm1d(out_ch),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.conv(x)


class InConv(nn.Module):

    def __init__(self, in_ch, out_ch):
        super(InConv, self).__init__()
        self.conv = DoubleBlock(in_ch, out_ch)

    def forward(self, x):
        return self.conv(x)


class Down(nn.Module):

    def __init__(self, in_ch, out_ch):
        super(Down, self).__init__()
        self.pool = nn.MaxPool1d(2, return_indices=True)
        self.block = DoubleBlock(in_ch, out_ch)

    def forward(self, x):
        x = self.block(x)
        x, indices = self.pool(x)
        return x, indices


class Up(nn.Module):

    def __init__(self, in_ch, out_ch):
        super(Up, self).__init__()
        self.unpool = nn.MaxUnpool1d(2)
        self.block = DoubleBlock(in_ch, out_ch)

    def forward(self, x, indices, output_shape):
        x = self.unpool(x, indices, output_shape)
        x = self.block(x)
        return x


class OutConv(nn.Module):

    def __init__(self, in_ch, out_ch):
        super(OutConv, self).__init__()
        self.conv = nn.Conv1d(in_ch, out_ch, 1)

    def forward(self, x):
        return self.conv(x)


class MicroFCN(nn.Module):

    def __init__(self, n_channels, n_classes):
        super(MicroFCN, self).__init__()
        self.inconv = InConv(n_channels, 16)
        self.down1 = Down(16, 32)
        self.up1 = Up(32, 16)
        self.outconv = OutConv(16, n_classes)

    def forward(self, x):
        x1 = self.inconv(x)
        x2, indices1 = self.down1(x1)
        x3 = self.up1(x2, indices1, x1.shape)
        x4 = self.outconv(x3)
        x5 = torch.sigmoid(x4)
        return x5
