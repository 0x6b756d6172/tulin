from fastai.widgets import *
from fastai.vision import *
from torch.utils.tensorboard import SummaryWriter
from datetime import datetime
import os

#learn.callbacks.append(FasterAICallback(learn, "", "", ""))

class Callback(Callback):
    def __init__(self, learn:Learner, primaryMetric, name, comment, maximize=False):
        super().__init__()
        now = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
        self.name = f"{now}-{name}-{comment}"
        self.learn = learn
        self.writer = SummaryWriter(f"./runs/{self.name}")
        self.epoch = 0
        self.iteration = 0 
        self.primaryMetric = primaryMetric
        self.maximize = maximize
        self.lastMetric = None
        self.lastEpoch = 0
        self.lastSavePath = ""
        
    def saveifbetter(self, last_metrics:MetricsList):
        i = self.learn.recorder.names[2:].index(self.primaryMetric)
        
        if self.lastMetric is None: 
            self.lastMetric = last_metrics[i]
            self.lastEpoch = self.epoch
            self.lastSavePath = self.learn.save(f"{self.name}-ep-{self.epoch}-val-{self.lastMetric}", return_path=True)
            
        current = last_metrics[i]
        better = current > self.lastMetric if self.maximize else current < self.lastMetric
        
        if better: 
            os.remove(self.lastSavePath) 
            self.lastMetric = current
            self.lastEpoch = self.epoch
            self.lastSavePath = self.learn.save(f"{self.name}-ep-{self.epoch}-val-{self.lastMetric}", return_path=True)
        
    def tb_write_model(self):
        input_to_model = next(iter(self.learn.data.dl(DatasetType.Single)))[0]
        self.writer.add_graph(self.learn.model, input_to_model)
        self.writer.flush()
    
    def tb_write_loss(self, last_loss:Tensor, train:bool):
        if not train: return
        if self.iteration != 0: 
            self.writer.add_scalar("batch/training_loss", last_loss, self.iteration)
            #values = [(name, values.clone().detach().cpu()) for (name, values) in self.learn.model.named_parameters()]
            #for name, value in values:
                #self.writer.add_histogram(f'weights/{name}', value, self.iteration)
        self.iteration += 1
    
    def tb_write_meterics(self, last_metrics:MetricsList):
        recorder = self.learn.recorder        
        for i, name in enumerate(recorder.names[2:]):
            if last_metrics is None or len(last_metrics) < i + 1: continue
            x = last_metrics[i]
            if type(x) == type(None): continue
            scalar_value = x.item()
            logName = f'epoch/{name}'
            self.writer.add_scalar(logName, scalar_value, self.epoch)
        self.writer.flush()
    
    def on_train_begin(self, **kwargs: Any) -> None:
        self.tb_write_model()
            
    def on_batch_end(self, last_loss:Tensor, train:bool, **kwargs)->None:
         self.tb_write_loss(last_loss, train)
    
    def on_epoch_end(self, last_metrics:MetricsList, train:bool, **kwargs)->None:
            if not train: 
                self.tb_write_meterics(last_metrics)
                self.saveifbetter(last_metrics)
                self.epoch += 1

