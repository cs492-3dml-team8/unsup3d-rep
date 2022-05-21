'''
under implementation
'''
import pstats
import torch
import torch.optim as optims
from torch.utils.data import DataLoader
#from torch.utils.tensorboard import SummaryWriter
from tensorboardX import SummaryWriter
from tqdm import tqdm
import time
import os.path as path
import os

from unsup3d.model import PhotoGeoAE
from unsup3d.dataloader import CelebA, BFM


# initially, 
LR = 1e-4
max_epoch = 200
load_chk = False
chk_PATH = './chk.pt'   # need to change later

is_debug = False

class Trainer():
    def __init__(self, configs, model = None): # model is for debug(05/09)
        '''initialize params (to be implemented)'''
        self.max_epoch = configs['num_epochs']
        self.img_size = configs['img_size']
        self.batch_size = configs['batch_size']
        self.learning_rate = configs['learning_rate']
        self.is_train = configs['run_train']

        self.epoch = 0
        self.step = 0
        self.best_loss = 1e10

        self.configs = configs

        '''path relevant'''
        now = time.localtime()
        curr_time = "%02d_%02d__%02d_%02d"&(now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
        self.exp_name = configs['exp_name_'] + curr_time
        self.exp_path = path.join(configs['exp_path'], self.exp_name)
        os.makedirs(self.exp_path, exist_ok=True)
        self.save_path = path.join(self.exp_path, 'models')
        os.makedirs(self.save_path, exist_ok=True)
        self.best_path = path.join(self.save_path, 'best.pt')
        self.load_path = None

        '''logger setting'''
        # self.writer = SummaryWriter('runs/fashion_mnist_experiment_1')
        self.writer = SummaryWriter(path.join(self.exp_path, 'logs'))
        self.save_epoch = configs['save_epoch']
        self.fig_epoch = configs['fig_plot_epoch']

        '''implement dataloader'''
        if configs['dataset'] == "celeba":
            self.datasets = CelebA(setting = 'train')
            self.val_datasets = CelebA(setting = 'val')
        elif configs['dataset'] == "bfm":
            self.datasets = BFM()
            self.val_datasets = None

        self.dataloader = DataLoader(
            self.datasets,
            batch_size= self.batch_size,
            shuffle=True,
            num_workers=4,
            drop_last=True,         # (05/20, inhee) I'm not sure currently we can handle last epoch properly
        )

        if self.val_datasets is not None:
            self.val_dataloader = DataLoader(
                self.val_datasets,
                batch_size= self.batch_size,
                shuffle=False,
                num_workers=4,
                drop_last=True,         # (05/20, inhee) I'm not sure currently we can handle last epoch properly
            )
        

        '''select GPU'''
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        '''define model'''
        if is_debug:
            self.model = model.to(self.device)                                  #### to debug
        else:
            self.model = PhotoGeoAE(configs).to(self.device)
        self.model.set_writer(self.writer)

        '''define optimizer and scheduler'''
        self.optimizer = optims.Adam(
            params = self.model.parameters(),
            lr = self.learning_rate
        )

        self.scheduler = optims.lr_scheduler.LambdaLR(
            optimizer = self.optimizer,
            lr_lambda = lambda epoch: 0.95 ** epoch
        )

        '''load_model and optimizer state'''
        if load_chk:
            self.load_model(self.load_path if self.load_path is not None else self.best_path)
        

    def train(self):
        init_epch = self.epoch
        for epch in range(init_epch, self.max_epoch):
            epch_loss = self._train()
            self.epoch = epch

            if epch_loss < self.best_loss:
                # save best model
                self.save_model(epch_loss)
                self.best_loss = epch_loss

            if self.epoch % self.save_epoch == 0:
                # save periodically
                self.save_model(epch_loss)

            self.writer.add_scalar("Loss_epch/train", epch_loss, self.epoch)

    def _train(self):
        '''train model (single epoch)'''
        epch_loss = 0
        cnt = 0
        for i, inputs in tqdm(enumerate(self.dataloader, 0)):
            inputs = inputs.to(self.device)
            losses = self.model(inputs, self.step)
            loss = torch.mean(losses)
            loss.backward()
            self.optimizer.step()

            # calculate epch_loss
            epch_loss += loss.detach().cpu()
            cnt += 1
            self.step += 1

            self.writer.add_scalar("Loss_step/train", loss.detach().cpu().item(), self.step)
        
        self.scheduler.step()
        return epch_loss
        # return epch_loss/cnt


    def load_model(self, PATH):
        '''
        save loaded model (05/08)
        '''
        chkpt = torch.load(PATH)
        self.model.load_state_dict(chkpt['model_state_dict'])
        self.optimizer.load_state_dict(chkpt['optimizer_state_dict'])
        self.epoch = chkpt['epoch']
        self.step = chkpt['step']
        self.best_loss = chkpt['loss']


    def save_model(self, loss):
        if loss < self.best_loss:
            PATH = path.join(self.save_path, 'best.pt')
        else:
            # saving chkpts periodically
            PATH = path.join(self.save_path, 'epoch_'+str(self.epoch)+'.pt')
        
        torch.save({
            'epoch': self.epoch,
            'step' : self.step,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'loss': loss,
            }, PATH)

        print("mode saved as ", PATH)



    def _val(self):
        '''validate model and plot testing images'''
        self.model.eval()

        with torch.no_grad():
            for i, inputs in tqdm(enumerate(self.val_dataloader, 0)):
                inputs = inputs.to(self.device)
                losses = self.model(inputs)
                



    def _test(self):
        '''test model'''
        pass