from environment import ThumperEnvironment
from sb3_contrib import MaskablePPO

environment = ThumperEnvironment(1)

model = MaskablePPO("MlpPolicy", environment, verbose=1, device="cpu")
model.learn(total_timesteps=10_000)

vec_env = model.get_env()
observation = vec_env.reset()
for i in range(1000):
	action_masks = environment.action_masks()
	action, _states = model.predict(observation, deterministic=True, action_masks=action_masks)
	observation, reward, done, info = vec_env.step(action)
	vec_env.render()

environment.close()