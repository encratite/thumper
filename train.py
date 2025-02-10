import os
import datetime
import pprint
import numpy as np
import torch
from torch import nn
from torch.distributions import Distribution, Independent, Normal
from torch.optim.lr_scheduler import LambdaLR
from gymnasium.spaces import Dict
from tianshou.env import DummyVectorEnv
from tianshou.data import Collector, VectorReplayBuffer
from tianshou.env.pettingzoo_env import PettingZooEnv
from tianshou.highlevel.logger import LoggerFactoryDefault
from tianshou.policy import PPOPolicy, MultiAgentPolicyManager
from tianshou.policy.base import BasePolicy
from tianshou.trainer import OnpolicyTrainer
from tianshou.utils.net.common import ActorCritic, Net
from tianshou.utils.net.continuous import Actor, Critic

import environment
from constants import Constant

def make_envs(count):
	def wrap_env():
		env = environment.env()
		wrapped = PettingZooEnv(env)
		return wrapped

	env = wrap_env()
	train_envs = DummyVectorEnv([wrap_env for _ in range(count)])
	test_envs = DummyVectorEnv([wrap_env for _ in range(count)])
	return env, train_envs, test_envs

def test_ppo():
	# Arguments
	task = "Thumper-v0"
	log_dir = "logs"
	environments = 5
	buffer_size = 4096
	hidden_sizes = [64, 64]
	lr = 3e-4
	lr_decay = True
	epochs = 100
	step_per_epoch = 10_000
	step_per_collect = 2048
	repeat_per_collect = 10
	episode_per_test = 8
	batch_size = 64
	device = "cpu"

	# Argument dictionary for logging
	args = {
		"task": task,
		"log_dir": log_dir,
		"environments": environments,
		"buffer_size": buffer_size,
		"hidden_sizes": hidden_sizes,
		"lr": lr,
		"lr_decay": lr_decay,
		"epochs": epochs,
		"step_per_epoch": step_per_epoch,
		"step_per_collect": step_per_collect,
		"repeat_per_collect": repeat_per_collect,
		"episode_per_test": episode_per_test,
		"batch_size": batch_size,
		"device": device
	}

	env, train_envs, test_envs = make_envs(environments)
	observation_space = (
		env.observation_space["observation"]
		if isinstance(env.observation_space, Dict)
		else env.observation_space
	)
	state_shape = observation_space.shape or int(observation_space.n)
	action_shape = env.action_space.shape or int(env.action_space.n)
	net = Net(state_shape=state_shape, hidden_sizes=hidden_sizes, device=device)
	actor: nn.Module
	critic: nn.Module
	actor = Actor(net, args.action_shape, device=args.device).to(args.device)
	critic = Critic(net, device=args.device).to(args.device)
	actor_critic = ActorCritic(actor, critic)
	torch.nn.init.constant_(actor.sigma_param, -0.5)
	for module in actor_critic.modules():
		if isinstance(module, torch.nn.Linear):
			torch.nn.init.orthogonal_(module.weight, gain=np.sqrt(2))
			torch.nn.init.zeros_(module.bias)
	for module in actor.mu.modules():
		if isinstance(module, torch.nn.Linear):
			torch.nn.init.zeros_(module.bias)
			module.weight.data.copy_(0.01 * module.weight.data)
	optim = torch.optim.Adam(actor_critic.parameters(), lr=lr)
	if lr_decay:
		max_update_num = np.ceil(step_per_epoch / step_per_collect) * epochs
		lr_scheduler = LambdaLR(optim, lr_lambda=lambda epoch: 1 - epoch / max_update_num)
	else:
		lr_scheduler = None

	def dist_fn(loc_scale: tuple[torch.Tensor, torch.Tensor]) -> Distribution:
		loc, scale = loc_scale
		return Independent(Normal(loc, scale), 1)

	agents = []
	for _ in range(Constant.PLAYER_COUNT):
		agent = PPOPolicy(
			actor=actor,
			critic=critic,
			optim=optim,
			dist_fn=dist_fn,
			lr_scheduler=lr_scheduler,
			action_space=env.action_space,
			action_scaling=False
		)
		agents.append(agent)
	policy = MultiAgentPolicyManager(policies=agents, env=env)

	buffer = VectorReplayBuffer(buffer_size, len(train_envs))
	train_collector = Collector(policy, train_envs, buffer, exploration_noise=True)
	test_collector = Collector(policy, test_envs)

	now = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
	log_name = os.path.join(task, now)
	log_path = os.path.join(log_dir, log_name)
	logger_factory = LoggerFactoryDefault()
	logger_factory.logger_type = "tensorboard"
	logger = logger_factory.create_logger(
		log_dir=log_path,
		experiment_name=log_name,
		config_dict=args,
		run_id=None
	)

	def save_best_fn(policy: BasePolicy) -> None:
		state = {
			"model": policy.state_dict(),
			"obs_rms": train_envs.get_obs_rms()
		}
		torch.save(state, os.path.join(log_path, "policy.pth"))

	trainer = OnpolicyTrainer(
		policy=policy,
		train_collector=train_collector,
		test_collector=test_collector,
		max_epoch=epochs,
		step_per_epoch=step_per_epoch,
		repeat_per_collect=repeat_per_collect,
		episode_per_test=episode_per_test,
		batch_size=batch_size,
		step_per_collect=step_per_collect,
		save_best_fn=save_best_fn,
		logger=logger,
		test_in_train=False,
	)
	result = trainer.run()
	pprint.pprint(result)

if __name__ == "__main__":
	test_ppo()