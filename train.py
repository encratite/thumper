import gymnasium as gym
from keras.models import Sequential, Model
from keras.layers import Input, Dense, Activation, Flatten, Reshape, Lambda
from keras.optimizers import Adam
from rl.agents.dqn import DQNAgent
from rl.policy import BoltzmannQPolicy
from rl.memory import SequentialMemory
from environment import ThumperEnvironment

environment = ThumperEnvironment(1)

# The input is a tuple (observation, info)
# input = Input(shape=(1, 2))
# Extract observation and ignore the info dict
# observation = input[:, :, 0]
# reshaped_observation = Reshape((1,) + environment.observation_space.shape)(observation)
# print(reshaped_observation.shape)

model = Sequential()
model.add(Flatten(input_shape=(1,) + environment.observation_space.shape))
model.add(Dense(32))
model.add(Activation("relu"))
model.add(Dense(16))
model.add(Activation("relu"))
model.add(Dense(8))
model.add(Activation("relu"))
model.add(Dense(environment.action_space.n))
model.add(Activation("linear"))

memory = SequentialMemory(limit=10000, window_length=1)
policy = BoltzmannQPolicy()
agent = DQNAgent(
	model=model,
	nb_actions=environment.action_space.n,
	memory=memory,
	nb_steps_warmup=10,
	target_model_update=1e-2,
	policy=policy
)
agent.compile(Adam(lr=1e-3), metrics=["mae"])
agent.fit(environment, nb_steps=1000, verbose=2)