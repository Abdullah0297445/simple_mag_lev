# -*- coding: utf-8 -*-
"""
Created on Sat Nov 10 21:41:59 2018

@author: 1FA5K1ER9
"""

import gym
from gym import wrappers
import random
import math
import torch
import torch.nn as nn
import torch.optim as optim
from torch.autograd import Variable
import torch.nn.functional as F
import matplotlib.pyplot as plt
from maglevEnv import MagLevEnv
import numpy as np


EPISODES = 50  # number of episodes
EPS_START = 0.9  # e-greedy threshold start value
EPS_END = 0.05  # e-greedy threshold end value
EPS_DECAY = 2000 # e-greedy threshold decay
GAMMA = 0.8  # Q-learning discount factor
LR = 0.001  # NN optimizer learning rate
HIDDEN_LAYER = 256  # NN hidden layer size
BATCH_SIZE = 64  # Q-learning batch size

# if gpu is to be used
use_cuda = torch.cuda.is_available()
FloatTensor = torch.cuda.FloatTensor if use_cuda else torch.FloatTensor
LongTensor = torch.cuda.LongTensor if use_cuda else torch.LongTensor
ByteTensor = torch.cuda.ByteTensor if use_cuda else torch.ByteTensor

Tensor = FloatTensor

class ReplayMemory:
    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = []

    def push(self, transition):
        self.memory.append(transition)
        if len(self.memory) > self.capacity:
            del self.memory[0]

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)


class Network(nn.Module):
    def __init__(self):
        nn.Module.__init__(self)
#        self.l1 = nn.Linear(3, HIDDEN_LAYER)
        self.l2 = nn.Linear(3, 16)
        self.l1 = nn.Linear(3, 2)

    def forward(self, x):
        #x = F.relu(self.l1(x))
        #x = F.relu(self.l2(x))
        x = self.l1(x)
        return x
    
env = MagLevEnv()
env.initialpos = 6.0
#env = wrappers.Monitor(env, './tmp/cartpole-v01')

model = Network()
if use_cuda:
    model.cuda()
memory = ReplayMemory(10000)
optimizer = optim.Adam(model.parameters(), LR)
steps_done = 0
episode_durations = []

def select_action(state,AlwaysUseNN = False):
    global steps_done
    sample = random.random()
    eps_threshold = EPS_END + (EPS_START - EPS_END) * math.exp(-1. * steps_done / EPS_DECAY)
    steps_done += 1
    if (sample > eps_threshold) or AlwaysUseNN:
        return model(Variable(state, volatile=True).type(FloatTensor)).data.max(1)[1].view(1, 1)
    else:
        return LongTensor([[random.randrange(2)]])


def run_episode(e, environment):
    state = environment.reset()
    steps = 0
    while True:
        #environment.render()
        action = select_action(FloatTensor([state]))
        #action = action.data.numpy()[0,0]

        #action = round(action)
        next_state, reward, done, _ = environment.step(action)
        action = np.array([action])
        
        # negative reward when attempt ends
  
#        if done:        
#            break
        memory.push((FloatTensor([state]),
                     FloatTensor([action]), 
                     FloatTensor([next_state]),
                     FloatTensor([reward])))

        learn()

        state = next_state
        steps += 1

        if done or steps>500:
            print('Episode %s finished after %s steps' %(e, steps))
            print(steps,state,reward,action,done)
            episode_durations.append(steps)
            #plot_durations()
            break


def learn():
    if len(memory) < BATCH_SIZE:
        return

    # random transition batch is taken from experience replay memory
    transitions = memory.sample(BATCH_SIZE)
    batch_state, batch_action, batch_next_state, batch_reward = zip(*transitions)

    batch_state = Variable(torch.cat(batch_state))
    batch_action = Variable(torch.cat(batch_action))
    batch_reward = Variable(torch.cat(batch_reward))
    batch_next_state = Variable(torch.cat(batch_next_state))

    # current Q values are estimated by NN for all actions
   
    #current_q_values = model(batch_state).max(1)[0]#gather(1, batch_action)
    current_q_values = model(batch_state)
    # expected Q values are estimated from actions which gives maximum Q value
    max_next_q_values = model(batch_next_state).detach().max(1)[0]
    expected_q_values = batch_reward + (GAMMA * max_next_q_values)
    #expected_q_values = expected_q_values.view(64,1)
    #x_train.view(101, 1)   

    # loss is measured from error between current and newly expected Q values
    loss = F.smooth_l1_loss(current_q_values, expected_q_values)

    # backpropagation of loss to NN
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

for e in range(EPISODES):
    run_episode(e, env)    

1/0
state = env.reset()
for i in range(100):
    action = select_action(FloatTensor([state]),AlwaysUseNN=True)
    a = action.data.numpy()[0,0]
    state,reward,done,_ = env.step(a)
    print(i,state,reward,a,done)
    env.render()
