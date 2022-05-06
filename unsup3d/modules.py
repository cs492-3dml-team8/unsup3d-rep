'''
Define all neural networks used in photo-geometric pipeline
Any learnable parameters shouldn't be defined out of this file
'''

import torch.nn as nn

# network architecture for viewpoint, lighting
class Encoder(nn.Module):
    def __init__(self, cout):
        '''
        Encoder:
            Conv(3, 32, 4, 2, 1) + ReLU 32
            Conv(32, 64, 4, 2, 1) + ReLU 16
            Conv(64, 128, 4, 2, 1) + ReLU 8
            Conv(128, 256, 4, 2, 1) + ReLU 4
            Conv(256, 256, 4, 1, 0) + ReLU 1
            Conv(256, cout, 1, 1, 0) + Tanh! output 1
        '''
        '''
        * view: cout = 6
        * lighting: cout = 4
        '''
        super(Encoder, self).__init__()

        # encoder network
        encoder = [
            nn.Conv2d(3, 32, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(128, 256, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(256, 256, kernel_size=4, stride=1, padding=0),
            nn.ReLU()
            nn.Conv2d(256, cout, kernel_size=1, stride=1, padding=0),
            nm.Tanh()
        ]
        self.encoder = nn.Sequential(*encoder)

    def forward(self, input):
        out = self.encoder(input)

        return out

# network architecture for depth, albedo
class AutoEncoder(nn.Module):
    def __init__(self, cout):
        '''
        Encoder: 
            Conv(3, 64, 4, 2, 1) + GN(16) + LReLU(0.2) 32
            Conv(64, 128, 4, 2, 1) + GN(32) + LReLU(0.2) 16
            Conv(128, 256, 4, 2, 1) + GN(64) + LReLU(0.2) 8
            Conv(256, 512, 4, 2, 1) + LReLU(0.2) 4
            Conv(512, 256, 4, 1, 0) + ReLU 1
        Decoder:
            Deconv(256, 512, 4, 1, 0) + ReLU 4
            Conv(512, 512, 3, 1, 1) + ReLU 4
            Deconv(512, 256, 4, 2, 1) + GN(64) + ReLU 8
            Conv(256, 256, 3, 1, 1) + GN(64) + ReLU 8
            Deconv(256, 128, 4, 2, 1) + GN(32) + ReLU 16
            Conv(128, 128, 3, 1, 1) + GN(32) + ReLU 16
            Deconv(128, 64, 4, 2, 1) + GN(16) + ReLU 32
            Conv(64, 64, 3, 1, 1) + GN(16) + ReLU 32

            Upsample(2) 64
            
            Conv(64, 64, 3, 1, 1) + GN(16) + ReLU 64
            Conv(64, 64, 5, 1, 2) + GN(16) + ReLU 64
            Conv(64, cout, 5, 1, 2) + Tanh! output 64
        '''

        '''
        * depth: cout=1
        * albedo: cout=3
        '''
        super(AutoEncoder, self).__init__()

        # encoder network
        encoder = [
            nn.Conv2d(3, 64, kernel_size=4, stride=2, padding=1),       # layer 1
            nn.GroupNorm(16, 64),
            nn.LeakyReLU(0.2),
            nn.Conv2d(64, 128, kernel_size=4, stride=2, padding=1),      # layer 2
            nn.GroupNorm(32, 128),
            nn.LeakyReLU(0.2),
            nn.Conv2d(128, 256, kernel_size=4, stride=2, padding=1),      # layer 3
            nn.GroupNorm(64, 256),
            nn.LeakyReLU(0.2),
            nn.Conv2d(256, 512, kernel_size=4, stride=2, padding=1),      # layer 4
            nn.LeakyReLU(0.2),
            nn.Conv2d(512, 256, kernel_size=4, stride=1, padding=0),      # layer 5
            nn.ReLU()
        ]

        # decoder network
        decoder = [
            nn.ConvTranspose2d(256, 512, kernel_size=4, stride=1, padding=0),
            nn.ReLU(),
            nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(512, 256, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(64, 256),
            nn.ReLU(),
            nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.GroupNorm(64, 256),
            nn.ReLU(),
            nn.ConvTranspose2d(256, 128, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(32, 128),
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.GroupNorm(32, 128),
            nn.ReLU(),
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(16, 64),
            nn.ReLU(),

            nn.Upsample(scale_factor=2),
            
            nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.GroupNorm(16, 64),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=5, stride=1, padding=2),
            nn.GroupNorm(16, 64),
            nn.ReLU(),
            nn.Conv2d(64, cout, kernel_size=5, stride=1, padding=2),
            nn.Tanh()
        ]

        self.encoder = nn.Sequential(*encoder)
        self.decoder = nn.Sequential(*decoder)

    def forward(self, input):
        out = self.encoder(input)
        out = self.decoder(out)

        return out

    
# network architecture for confidence map
class Conf_Conv(nn.Module):
    def __init__(self):
        '''
        Encoder: 
            Conv(3, 64, 4, 2, 1) + GN(16) + LReLU(0.2) 32
            Conv(64, 128, 4, 2, 1) + GN(32) + LReLU(0.2) 16
            Conv(128, 256, 4, 2, 1) + GN(64) + LReLU(0.2) 8
            Conv(256, 512, 4, 2, 1) + LReLU(0.2) 4
            Conv(512, 128, 4, 1, 0) + ReLU 1
        Decoder:
            Deconv(128, 512, 4, 1, 0) + ReLU 4
            Deconv(512, 256, 4, 2, 1) + GN(64) + ReLU 8
            Deconv(256, 128, 4, 2, 1) + GN(32) + ReLU 16
                Conv(128, 2, 3, 1, 1) + SoftPlus! --> output 16
            Deconv(128, 64, 4, 2, 1) + GN(16) + ReLU 32
            Deconv(64, 64, 4, 2, 1) + GN(16) + ReLU 64
            Conv(64, 2, 5, 1, 2) + SoftPlus! --> output 64
        '''

        '''
        `Conf_Conv` outputs two pairs of confidence maps at different
        spatial resolutions for i) photometric and ii) perceptual losses
        '''
        encoder = [
            nn.Conv2d(3, 64, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(16, 64),
            nn.LeakyReLU(0.2),
            nn.Conv2d(64, 128, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(32, 128),
            nn.LeakyReLU(0.2),
            nn.Conv2d(128, 256, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(64, 256),
            nn.LeakyReLU(0.2),
            nn.Conv2d(256, 512, kernel_size=4, stride=2, padding=1),
            nn.LeakyReLU(0.2),
            nn.Conv2d(512, 128, kernel_size=4, stride=1, padding=0),
            nn.ReLU()
        ]

        decoder_1 = [
            nn.ConvTranspose2d(128, 512, kernel_size=4, stride=1, padding=0),
            nn.ReLU(),
            nn.ConvTranspose2d(512, 256, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(64, 256),
            nn.ReLU(),
            nn.ConvTranspose2d(256, 128, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(32, 128),
            nn.ReLU()
        ]

        out_1 = [
            nn.Conv2d(128, 2, kernel_size=3, stride=1, padding=1),
            nn.SoftPlus()
        ]

        decoder_2 = [
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(16, 64),
            nn.ReLU(),
            nn.ConvTranspose2d(64, 64, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(16, 64),
            nn.ReLU(),
            nn.Conv2d(64, 2, kernel_size=5, stride=1, padding=2)
        ]

        self.encoder = nn.Sequential(*encoder)
        self.decoder_1 = nn.Sequential(*decoder_1)
        self.out_1 = nn.Sequential(*out_1)
        self.decoder_2 = nn.Sequential(*decoder_2)

    def forward(self, input):
        out = self.encoder(input)
        out = self.decoder_1(out)
        out_1 = self.out_1(out)
        out_2 = self.decoder_2(out)
        
        return out_1, out_2



'''
# make a convolutional block (conv + normalization + activation)
def conv_block(in_channels, 
                out_channels, 
                conv_type='conv', 
                kernel_size=4,  
                stride=1, 
                padding=0,
                norm='gn',
                n_groups=1,
                activation='relu',
                leaky_rate=0.2):

    block = []

    # 1) add a conv (or deconv) layer
    if conv_type == 'conv':
        block += [nn.Conv2d(in_channels, out_channels, 
                    kernel_size=kernel_size, stride=stride, padding=padding)]
    elif conv_type == 'deconv':
        block += [nn.ConvTranspose2D(in_channels, out_channels, 
                    kernel_size=kernel_size, stride=stride, padding=padding)]

    # 2) add a normalization function
    if norm is not None:
        if norm == 'gn'         # group norm
            block += [nn.GroupNorm(n_groups, out_channels)]

    # 3) add an activation function
    if activation == 'relu':
        block += [nn.ReLU()]
    elif activation == 'leaky':
        block += [nn.LeakyReLU(leaky_rate)]

    return block
'''