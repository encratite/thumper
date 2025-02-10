import os
import datetime
import pprint
import numpy as np
import torch
from torch import nn
from torch.distributions import Distribution, Independent, Normal
from torch.optim.lr_scheduler import LambdaLR
from tianshou.env import DummyVectorEnv
from tianshou.data import Collector, CollectStats, ReplayBuffer, VectorReplayBuffer
from tianshou.highlevel.logger import LoggerFactoryDefault
from tianshou.policy import PPOPolicy
from tianshou.policy.base import BasePolicy
from tianshou.trainer import OnpolicyTrainer
from tianshou.utils.net.common import ActorCritic, Net
from tianshou.utils.net.continuous import ActorProb, Critic

import environment

def make_envs(count):
	env = environment.env()
	train_envs = DummyVectorEnv([environment.env for _ in range(count)])
	test_envs = DummyVectorEnv([environment.env for _ in range(count)])
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
	state_shape, action_shape = env.get_shapes()
	net_a = Net(
		state_shape,
		hidden_sizes=hidden_sizes,
		activation=nn.Tanh,
		device=device
	)
	actor = ActorProb(
		net_a,
		action_shape,
		unbounded=True,
		device=device
	).to(device)
	net_c = Net(
		state_shape,
		hidden_sizes=hidden_sizes,
		activation=nn.Tanh,
		device=device
	)
	critic = Critic(net_c, device=device).to(device)
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
	action_space = env.get_action_space()

	def dist_fn(loc_scale: tuple[torch.Tensor, torch.Tensor]) -> Distribution:
		loc, scale = loc_scale
		return Independent(Normal(loc, scale), 1)

	policy = PPOPolicy(
		actor=actor,
		critic=critic,
		optim=optim,
		dist_fn=dist_fn,
		lr_scheduler=lr_scheduler,
		action_space=action_space,
		action_scaling=False
	)

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