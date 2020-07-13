import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

from torch.utils.data import Dataset
from torch.utils.data import DataLoader

import numpy as np

from src import TextGenerator
from utils import Preprocessing

file = 'data/book.txt'
window = 20

class DatasetMaper(Dataset):
	'''
	Handles batches of dataset
	'''
	def __init__(self, x, y):
		self.x = x
		self.y = y
		
	def __len__(self):
		return len(self.x)
		
	def __getitem__(self, idx):
		return self.x[idx], self.y[idx]


def train(sequences, targets):

	model = TextGenerator()

	training_set = DatasetMaper(sequences, targets)
	loader_training = DataLoader(training_set, batch_size=64)
	
	optimizer = optim.Adam(model.parameters(), lr=0.01)
	
	for epoch in range(200):
	
		predictions = []
		
		model.train()
		
		for x_batch, y_batch in loader_training:

			x = x_batch.type(torch.LongTensor)
			y = y_batch.type(torch.LongTensor)
		
			y_pred = model(x)
			
			loss = F.cross_entropy(y_pred, y.squeeze())
				
			optimizer.zero_grad()
				
			loss.backward()
				
			optimizer.step()
			
			y_pred_idx = y_pred.squeeze().detach().numpy()
			predictions += list(np.argmax(y_pred_idx, axis=1))
			
		acc = accuracy(targets, predictions)
		print("Epoch: %d,  loss: %.5f, accuracy: %.5f " % (epoch, loss.item(), acc))
		
	torch.save(model.state_dict(), 'textGenerator.pt')
			
def accuracy(y_true, y_pred):
	tp = 0
	for true, pred in zip(y_true, y_pred):
		if true == pred:
			tp += 1
			
	return tp / len(y_true)
	
def generator(model, x, idx_to_char):
	
	model.eval()
	
	softmax = nn.Softmax(dim=1)
	
	start = np.random.randint(0, len(x)-1)
	pattern = x[start]
	print("Seed:")
	print("\"", ''.join([idx_to_char[value] for value in pattern]), "\"")
	
	full_prediction = pattern.copy()
	for i in range(1000):
	
		pattern = torch.from_numpy(pattern).type(torch.LongTensor)
		pattern = pattern.view(1,-1)
		
		prediction = model(pattern)
		prediction = softmax(prediction)
		
		prediction = prediction.squeeze().detach().numpy()
		arg_max = np.argmax(prediction)
		
		pattern = pattern.squeeze().detach().numpy()
		pattern = pattern[1:]
		pattern = np.append(pattern, arg_max)
		full_prediction = np.append(full_prediction, arg_max)
		
	print("Prediction: ")
	print("\"", ''.join([idx_to_char[value] for value in full_prediction]), "\"")

if __name__ == '__main__':

	preprocessing = Preprocessing()
	text = preprocessing.read_dataset(file)
	char_to_idx, idx_to_char = preprocessing.create_dictionary(text)
	x, y = preprocessing.build_sequences_target(text, char_to_idx, window=window)

	vocab_len = len(char_to_idx)
	
	sequences = x.copy()
	targets = y.copy()
	
	# Training
	train(sequences, targets)
	
	# Loading models and restarting weights
	model = TextGenerator()
	model.load_state_dict(torch.load('textGenerator.pt'))
	generator(model, x, idx_to_char)