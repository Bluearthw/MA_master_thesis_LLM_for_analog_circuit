import gymnasium as gym
from gymnasium.spaces import Box
import numpy as np
import os
import yaml
import math
import shutil
import utils.saving as saving
from ngspice_interface import DUT as DUT_NGSpice
from utils.plotting import plotLearning, plot_running_maximum, solutions2pareto
from genai_agent import local_config

class CircuitEnv(gym.Env):
    PER_LOW, PER_HIGH = -np.inf, +np.inf
    
    def __init__(self, config=None, circuit_name='TwoStage', run_id='rllib_baseline',
                 success_threshold=0.0, simulator='ngspice'):
        self.run_id = run_id
        self.max_steps_per_episode = 10
        self.env_steps = 0
        self.episode_steps = 0
        self.success_threshold = success_threshold
        self.circuit_name = circuit_name

        project_path = os.getcwd()
        yaml_directory = os.path.join(project_path, f"{simulator}_interface", 'files', 'yaml_files')
        circuit_yaml_path = os.path.join(yaml_directory, f'{circuit_name}.yaml')
        with open(circuit_yaml_path, 'r') as f:
            yaml_data = yaml.load(f, Loader=yaml.Loader)
        
        self.dict_params = yaml_data['params']
        self.dict_targets = yaml_data['targets']
        self.hard_constraints = yaml_data['hard_constraints']
        self.optimization_targets = yaml_data['optimization_targets']

        self.n_actions = len(self.dict_params)
        self.obs_dim = len(self.dict_targets)

        # build param range dictionary
        self.param_ranges = {}
        for name, value in self.dict_params.items():
            self.param_ranges[name] = {'min': value[0], 'max': value[1], 'step': value[2]}
        
        self.simulation_engine = DUT_NGSpice(circuit_yaml_path)
        # self.simulation_engine.output_files_folder = local_config.path_output

        print(f"\n Initialized {circuit_name} with simulator {simulator} \n")

        # Action / observation spaces
        act_high = np.array([1 for _ in range(self.n_actions)])
        act_low = np.array([-1 for _ in range(self.n_actions)])
        self.action_space = Box(low=act_low, high=act_high)
        obs_high = np.array([CircuitEnv.PER_HIGH]*self.obs_dim, dtype=np.float32)
        obs_low = np.array([CircuitEnv.PER_LOW]*self.obs_dim, dtype=np.float32)
        self.observation_space = Box(low=obs_low, high=obs_high)

        self.spec_weights = yaml_data['spec_weights']
        self.reward_history = []
        self.score_history = []
        self.counter = 0
        self.pvt_corner = {'process': 'TT', 'voltage': 1.2, 'temp': 27}


    def action_refine(self, action):
        """
        TODO: Implement a function that converts normalized actions to actual parameter values.
        
        This function should:
        1. Take a flattened numpy array of actions (values between -1 and 1)
        2. Convert each action value to the actual parameter value from self.parameter_ranges
        
        You have two options;
            1) Continuous mapping: convert the action directly to the parameter value based on the min-max values
            2) Discretize mapping: create a vector of possible values using the min-max-step from self.parameter_ranges, 
                                    then, map the action to an index of that vector and retreive the corresponding actual value.

        Args:
            action: numpy array of normalized values between -1 and 1
            
        Returns:
            dict: Dictionary mapping parameter names to their actual sizing values
                e.g., {'mp1': 13, 'wp1':2.0e-06, 'lp1':9.0e-08, ...}
        
        """
        # Continuous， smoother gradient? too much data? values sometime looks strange.
        # D, Simpler for the AI to learn early on， values look more meaningful
        action_flat = np.array(action).flatten()
        param_list = {}
        for i, (l_name, l_range) in enumerate(self.param_ranges.items()):
            min_val = l_range['min']
            max_val = l_range['max']
            value = (action_flat[i] / 2) * (max_val - min_val) + min_val + (max_val - min_val)/2
            if l_name.__contains__('m'):
                value = int(value)
            param_list[l_name] = value
        return param_list


    def simulate(self, params):
        project_path = os.getcwd()
        yaml_path = os.path.join(project_path, 'ngspice_interface', 'files', 'yaml_files', 'TwoStage.yaml')

        try:
            dut = DUT_NGSpice(yaml_path)
            dut.output_files_folder = "./no_backup/output_files"
            process = self.pvt_corner['process']
            temp_pvt = self.pvt_corner['temp']
            vdd = self.pvt_corner['voltage']

            # Create and simulate new netlist
            new_netlist_path = dut.create_new_netlist(params, process, temp_pvt, vdd)
            dut.netlist_path = new_netlist_path   # <-- ADD THIS LINE
            info = dut.simulate(new_netlist_path) # True of false
            dut.random_name = "TwoStage"
            print(f"New netlist created at: {new_netlist_path}")
            print("VDD:", dut.VDD)

            # Measure specs
            spec_dict = dut.measure_metrics()
            self.last_netV = spec_dict.get('netV', None) #？？？？ it it none

            # Keep DUT and its unique netlist path
            self.simulation_engine = dut
            self.simulation_engine.netlist_path = new_netlist_path  # <-- ADD THIS LINE TOO

        except Exception as e:
            print(f"[Warning] Simulation failed: {e}")
            spec_dict = {key: 0.0 for key in self.dict_targets.keys()}

        return spec_dict



    def normalize_specs(self, spec_dict):
        norm_dict = {}
        for key, value in spec_dict.items():
            if isinstance(value, (dict, list, np.ndarray)):
                continue
            goal = self.dict_targets[key]
            if not np.isfinite(value) or not np.isfinite(goal):
                norm_dict[key] = 0.0# maybe we can treat it better like larger than goal set it inf 1 and --inf -1 
            else:
                k = value + goal if (value + goal) != 0 else 1e-9
                norm_dict[key] = (value - goal) / k
        return norm_dict


    def evaluate(self, action):
        self.param_values = self.action_refine(action)
        self.real_specs = self.simulate(self.param_values)
        self.cur_norm_specs = self.normalize_specs(self.real_specs)


    def reset(self, *, seed=None, options=None):
        self.episode_steps = 0
        action = np.random.uniform(-1, 1, [self.n_actions])
        self.evaluate(action)
        self.score = 0.0
        observation = np.concatenate([np.ravel(v) for v in self.cur_norm_specs.values()]).astype(np.float32)
        observation = np.nan_to_num(observation, nan=0.0, posinf=1e6, neginf=-1e6)
        """
         This method performs the following steps:
        1. Initializes the episode steps counter to zero.
        2. Generates a random action within the range [-1, 1] for each action parameter.
        3. Evaluates the environment with the generated random action.
        4. Resets the episode score to zero.
        5. Constructs the initial observation by returning the normalized current specifications.

        Note:
        - The observation is returned as a NumPy array of type float32.
        """
        return observation


    def step(self, action):
        """
        TODO: Perform a single step in the environment using the given action.

        This function should:
        1. Evaluate the given action.
        2. Compute the reward and check if the hard constraints are satisfied.
        3. Update the current observation.
        4. Append the reward to the reward history and update the score.
        5. Create output directories if they do not exist.
        6. If the goal state is reached, plot the running maximum reward.
        7. Increment the environment and episode step counters.
        8. Check if the maximum steps per episode have been reached, setting the done flag if true.
        9. Every 10 steps, update the score history, also plot the learning curve, and reset the score.
        10. Return the current observation, reward, done flag, and additional information.

        Args:
            action: The action to be taken in the environment. An array of values between -1 and 1.

        Returns:
            tuple: A tuple containing:
            - ob (np.ndarray): The current observation of the environment.
            - reward (float): The reward obtained from taking the action.
            - done (bool): A flag indicating whether the episode has ended.
            - info (dict): Additional information, including whether the goal state was reached.
        """
        self.evaluate(action)
        reward, hard_satisfied = self.reward_computation(self.cur_norm_specs)
        ob = np.array(list(self.cur_norm_specs.values()), dtype=np.float32)

        self.reward_history.append(reward)
        self.score += reward

        os.makedirs("./no_backup/output_files", exist_ok=True)
        os.makedirs(f"./output_figs/{self.run_id}/", exist_ok=True)
        os.makedirs(f"./solutions/{self.run_id}/", exist_ok=True)

        if hard_satisfied:
            plot_running_maximum(self.reward_history, self.run_id)
            csvName = saving.save_solutions_csv(self.run_id, self.env_steps, self.param_values, self.real_specs, reward)
            solutions2pareto(csvName, self.run_id, True)

            # =======================
            # Copy Pareto netlist here
            # =======================
            try:
                netlist_path = getattr(self.simulation_engine, "netlist_path", None)
                if netlist_path and os.path.isfile(netlist_path):
                    save_dir = os.path.join(f"./solutions/{self.run_id}/allRLcir/")
                    os.makedirs(save_dir, exist_ok=True)
                    target_path = os.path.join(save_dir, f"pareto_step_{self.env_steps}.cir")
                    shutil.copy(netlist_path, target_path)
                    print(f"[CircuitEnv] Saved Pareto netlist to {target_path}")
                else:
                    print("[CircuitEnv] Warning: No valid netlist found to copy.")
            except Exception as e:
                print(f"[CircuitEnv] Failed to copy Pareto netlist: {e}")

        self.env_steps += 1
        self.episode_steps += 1

        done = self.episode_steps >= self.max_steps_per_episode

        if self.env_steps % 10 == 0:
            self.score_history.append(self.score)
            plotLearning(self.score_history, self.run_id)
            self.score = 0.0

        info = {'goal_reached': hard_satisfied}
        return ob, reward, done, info


    def reward_computation(self, norm_specs):
        reward = 0.0
        rH = 0.0
        hard_satisfied = False

        for key in self.hard_constraints:
            val = norm_specs.get(key, 0.0)
            target = self.dict_targets.get(key, 0.0)
            if key in ["noise", "current", "area"]: # actually, only noise
                ry = -max(val, 0.0)
                rH += ry
            else:
                ry = min(val, 0.0)
                rH += ry

        rT = 0
        for key in self.optimization_targets:
            val = norm_specs.get(key, 0.0)
            rt = -val # current?
            rT += rt

        if rH < 0: # not met
            reward = rH + 0.05 * rT # rT is not the most important
        else:
            reward = 0.3 + rT
            hard_satisfied = True

        return reward, hard_satisfied


if __name__ == '__main__':
    env = CircuitEnv(
        circuit_name='TwoStage',
        run_id=0,
        simulator='ngspice',
        success_threshold=0.0
    )
    print(env.action_space)
    print(env.observation_space)

    ob = env.reset()
    print("Initial observation: ", ob)
    print("Initial parameters: ", env.param_values)
    print("Initial specs: ", env.real_specs)

    action = np.random.uniform(-1, 1, [env.n_actions])
    ob, reward, done, info = env.step(action)
    print("Next parameters: ", env.param_values)
    print("Next observation: ", ob)
    print("Next specs: ", env.real_specs)
    print("Reward: ", reward)
    print("Done: ", done)
