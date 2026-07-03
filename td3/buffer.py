import numpy as np
import torch


class ReplayBuffer(object):
	def __init__(self, state_dim, action_dim, max_size=int(1e6), num_rewards=1):
		self.max_size = max_size
		self.ptr = 0
		self.size = 0
		self.state_dim = state_dim
		self.action_dim = action_dim
		self.num_rewards = num_rewards

		self.state = np.zeros((max_size, state_dim), dtype=np.float32)
		self.action = np.zeros((max_size, action_dim), dtype=np.float32)
		self.next_state = np.zeros((max_size, state_dim), dtype=np.float32)
		self.reward = np.zeros((max_size, num_rewards), dtype=np.float32)
		self.not_done = np.zeros((max_size, 1), dtype=np.float32)

		self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

	def _prepare_vector(self, value, expected_dim, name):
		arr = np.asarray(value, dtype=np.float32).reshape(-1)
		if arr.size != expected_dim:
			print(f"{name} has shape {arr.shape}; expected ({expected_dim},)")
			raise ValueError(f"{name} has shape {arr.shape}; expected ({expected_dim},)")
		return arr

	def push(self, state, action, reward, next_state, done):
		prepared_state = self._prepare_vector(state, self.state_dim, "state")
		prepared_next_state = self._prepare_vector(next_state, self.state_dim, "next_state")
		prepared_action = self._prepare_vector(action, self.action_dim, "action")
		prepared_reward = self._prepare_vector(reward, self.num_rewards, "reward")

		self.action[self.ptr] = prepared_action
		self.state[self.ptr] = prepared_state
		self.next_state[self.ptr] = prepared_next_state
		self.reward[self.ptr] = prepared_reward.reshape(1, -1) if self.num_rewards > 1 else prepared_reward
		self.not_done[self.ptr] = 1.0 - float(done)

		self.ptr = (self.ptr + 1) % self.max_size
		self.size = min(self.size + 1, self.max_size)

	def sample(self, batch_size):
		if self.size == 0:
			raise ValueError("Cannot sample from an empty replay buffer")

		ind = np.random.randint(0, self.size, size=batch_size)
		return (
			torch.FloatTensor(self.state[ind]).to(self.device),
			torch.FloatTensor(self.action[ind]).to(self.device),
			torch.FloatTensor(self.next_state[ind]).to(self.device),
			torch.FloatTensor(self.reward[ind]).to(self.device),
			torch.FloatTensor(self.not_done[ind]).to(self.device),
		)