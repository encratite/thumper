from environment import ThumperEnvironment
from stable_baselines3 import PPO

environment = ThumperEnvironment(1)

model = PPO("MlpPolicy", environment, verbose=1, device="cpu")
model.learn(total_timesteps=10_000)

vec_env = model.get_env()
obs = vec_env.reset()
for i in range(1000):
	action, _states = model.predict(obs, deterministic=True)
	obs, reward, done, info = vec_env.step(action)
	vec_env.render()

environment.close()