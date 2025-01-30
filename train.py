from os import path
from environment import ThumperEnvironment
from sb3_contrib import MaskablePPO
from constants import *

def get_positions():
	positions = range(1, PLAYER_COUNT + 1)
	return positions

def get_model_name(position):
	model_name = f"Thumper (player {position})"
	return model_name

def get_model_path(position):
	model_name = get_model_name(position)
	model_path = path.join("model", model_name)
	return model_path

def load_model(position, environment=None):
	model_path = get_model_path(position)
	model_zip = f"{model_path}.zip"
	if path.exists(model_zip):
		model = MaskablePPO.load(model_path, env=environment)
		return model
	else:
		return None

def load_opponent_models():
	models = []
	positions = get_positions()
	for position in positions:
		model = load_model(position)
		if model is None:
			return None
		models.append(model)
	return models

def train_model(position, bootstrap):
	opponent_models = load_opponent_models()
	environment = ThumperEnvironment(position, opponent_models)
	model_name = get_model_name(position)
	model_path = get_model_path(position)
	model = load_model(position, environment)
	if model is None:
		model = MaskablePPO(
			"MlpPolicy",
			environment,
			learning_rate=1e-3,
			device="cpu",
			tensorboard_log="./tensorboard"
		)
	elif bootstrap:
		print(f"Model \"{model_name}\" has already been trained, skipping bootstrapping")
		return
	if opponent_models is None:
		print(f"Training model \"{model_name}\" using bootstrapping")
	else:
		print(f"Training model \"{model_name}\" using pre-trained opponent models")
	model.learn(
		total_timesteps=20_000 if bootstrap else 10_000,
		progress_bar=True,
		tb_log_name=model_name
	)
	environment.close()
	print(f"Saving model to {model_path}")
	model.save(model_path)

def train_models():
	positions = get_positions()
	for position in positions:
		train_model(position, True)
	for position in positions:
		train_model(position, False)

train_models()