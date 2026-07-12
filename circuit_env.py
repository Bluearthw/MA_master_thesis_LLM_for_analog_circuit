import gymnasium as gym
from gymnasium.spaces import Box
import numpy as np
import os
import json
import yaml
import math
import shutil
import time
import utils.file_utils as file_utils
from ngspice_interface import DUT as DUT_NGSpice
from utils.plotting import plotLearning, plot_running_maximum, solutions2pareto
# from genai_agent.data.local_config import list_targets_to_min

class CircuitEnv(gym.Env):
    PER_LOW, PER_HIGH = -np.inf, +np.inf
    
    def __init__(self, config=None, circuit_name='TwoStage', run_id='rllib_baseline',
                 success_threshold=0.0, simulator='ngspice', list_min_targets=None):
        self.run_id = run_id
        self.max_steps_per_episode = 10
        self.env_steps = 0
        self.episode_steps = 0
        self.success_threshold = success_threshold
        self.circuit_name = circuit_name

        project_path = os.getcwd()
        yaml_directory = os.path.join(project_path, f"{simulator}_interface", 'files', 'yaml_files')
        circuit_yaml_path = os.path.join(yaml_directory, f'{circuit_name}.yaml')
        self.output_files_dir = os.path.join(project_path, "no_backup", "output_files")
        self.output_figs_dir = os.path.join(project_path, "output_figs", str(self.run_id))
        self.solutions_dir = os.path.join(project_path, "solutions", str(self.run_id))
        self.all_rl_cir_dir = os.path.join(self.solutions_dir, "allRLcir")
        self.best_netlist_target_path = os.path.join(    self.solutions_dir, "best_so_far.cir")
        self.best_metadata_path = os.path.join(    self.solutions_dir, "best_so_far.json")

        for directory in (
            self.output_files_dir,
            self.output_figs_dir,
            self.solutions_dir,
            self.all_rl_cir_dir,
        ):
            os.makedirs(directory, exist_ok=True)
        # list_target_min_path = os.path.join

        with open(circuit_yaml_path, 'r') as f:
            yaml_data = yaml.load(f, Loader=yaml.Loader)
            self.path_circuit_yaml = circuit_yaml_path
        
        # self.data_for_dut = yaml_data['dut_config']
        self.list_min_targets = list_min_targets or []
        self.dict_params = yaml_data['params']
        self.dict_targets = yaml_data['targets']
        self.hard_constraints = yaml_data['hard_constraints']
        self.optimization_targets = yaml_data['optimization_targets']
        self.path_ids = yaml_data['path_id']
        self.n_actions = len(self.dict_params)
        self.obs_dim = len(self.dict_targets)
        # print(self.dict_params)
        # print(self.hard_constraints)
        # build param range dictionary
        self.param_ranges = {}
        for name, value in self.dict_params.items():
            self.param_ranges[name] = {'min': value[0], 'max': value[1], 'step': value[2]}
        
        self.simulation_engine = DUT_NGSpice(circuit_yaml_path)

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
        self.best_reward = -np.inf
        self.best_params = None
        self.best_specs = None
        self.best_step = None
        self.best_hard_satisfied = False
        self.best_netlist_path = None
        self.full_simulations = 0
        self.low_fidelity_simulations = 0
        self.seed_full_simulations = 0
        self.first_success_full_simulations = None
        self.run_start_time = time.time()
        self.time_to_first_solution_seconds = None
        self.time_to_best_solution_seconds = None
        self.best_source = None
        self.candidate_history = []


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


    def simulate(self, params, analysis_mode="full"):
        yaml_path = self.path_circuit_yaml
        info = None
        if analysis_mode == "full":
            self.full_simulations += 1
        else:
            self.low_fidelity_simulations += 1
        try:
            dut = DUT_NGSpice(yaml_path)
            dut.output_files_folder = self.output_files_dir
            process = self.pvt_corner['process']
            temp_pvt = self.pvt_corner['temp']
            vdd = self.pvt_corner['voltage']

            # Create and simulate new netlist
            new_netlist_path = dut.create_new_netlist(params, process, temp_pvt, vdd, analysis_mode=analysis_mode)
            print(f"New netlist created at: {new_netlist_path}")
            dut.netlist_path = new_netlist_path   # <-- ADD THIS LINE
            info = dut.simulate(new_netlist_path) # True of false
            
            dut.random_name = self.circuit_name
            # print("VDD:", dut.VDD)
            
            # Measure specs
            # print("CE: self path ids",self.path_ids)
            if analysis_mode in ("op", "op_ac"):
                spec_dict = self._measure_low_fidelity_specs()
            else:
                spec_dict = dut.measure_metrics(self.path_ids)
            self.last_netV = spec_dict.get('netV', None) #？？？？ it it none

            # Keep DUT and its unique netlist path
            self.simulation_engine = dut
            self.simulation_engine.netlist_path = new_netlist_path  # <-- ADD THIS LINE TOO

        except Exception as e:
            print(f"[Warning] Simulation failed: {e}")
            if info is not None:
                print(f"Simulation info: {info}")
            spec_dict = {key: 0.0 for key in self.dict_targets.keys()}

        return spec_dict

    def _dc_output_path(self):
        for spec_id, data_path in self.path_ids.items():
            if int(spec_id) in (22, 23):
                return data_path
        return None

    def _read_op_dc_values(self):
        dc_path = self._dc_output_path()
        if not dc_path or not os.path.exists(dc_path):
            return None
        try:
            data = np.genfromtxt(dc_path, autostrip=True, skip_header=1)
        except Exception as exc:
            print(f"[CircuitEnv] Failed reading OP/DC data {dc_path}: {exc}")
            return None

        arr = np.asarray(data, dtype=np.float64)
        if arr.size == 0:
            return None
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        return arr[-1]

    def _measure_low_fidelity_specs(self):
        spec_dict = {}
        if 0 in self.path_ids:
            try:
                spec_dict["dc_gain"] = float(self.simulation_engine.get_dc_gain_VV(self.path_ids[0]))
            except Exception as exc:
                print(f"[CircuitEnv] Failed reading low-fidelity DC gain: {exc}")
        op_device_metrics = self._read_op_device_metrics()
        if op_device_metrics:
            spec_dict.update(op_device_metrics)
        return spec_dict

    def _read_op_device_metrics(self):
        device_path = getattr(self.simulation_engine, "op_device_path", None)
        if not device_path or not os.path.exists(device_path):
            return {}
        try:
            data = np.genfromtxt(device_path, autostrip=True, skip_header=1)
        except Exception as exc:
            print(f"[CircuitEnv] Failed reading OP device data {device_path}: {exc}")
            return {}

        arr = np.asarray(data, dtype=np.float64)
        if arr.size == 0:
            return {}
        if arr.ndim == 1:
            values = arr
        else:
            values = arr[-1]

        # wrdata emits x/y pairs for each vector. Keep the value columns.
        if values.size % 2 == 0:
            values = values[1::2]

        if values.size < 5:
            return {}

        device_values = values[: (values.size // 5) * 5].reshape(-1, 5)
        vds = device_values[:, 0]
        vgs = device_values[:, 1]
        vth = device_values[:, 2]
        gm = device_values[:, 3]
        ids = device_values[:, 4]

        finite_rows = np.all(np.isfinite(device_values), axis=1)
        alive_rows = finite_rows & (np.abs(gm) > 1e-12) & (np.abs(ids) > 1e-12)
        overdrive = np.abs(vgs - vth)
        saturation_rows = alive_rows & (np.abs(vds) + 1e-12 >= overdrive)

        total = int(device_values.shape[0])
        alive_count = int(np.count_nonzero(alive_rows))
        saturation_count = int(np.count_nonzero(saturation_rows))
        return {
            "op_device_count": total,
            "op_alive_count": alive_count,
            "op_saturation_count": saturation_count,
            "op_alive_ratio": float(alive_count / total) if total else 0.0,
            "op_saturation_ratio": float(saturation_count / total) if total else 0.0,
            "op_mean_abs_gm": float(np.mean(np.abs(gm[finite_rows]))) if np.any(finite_rows) else 0.0,
        }

    def ac_gain_reward(self, spec_dict):
        dc_gain = spec_dict.get("dc_gain")
        if dc_gain is None or not np.isfinite(dc_gain):
            return -1.0

        gain = abs(float(dc_gain))
        if gain <= 0.0:
            return -1.0

        target = float(self.dict_targets.get("dc_gain", 1.0))
        target = max(target, 1e-12)
        return float((gain - target) / (gain + target + 1e-12))

    def op_domain_reward(self, spec_dict):
        device_count = int(spec_dict.get("op_device_count", 0) or 0)
        if device_count <= 0:
            return -1.0

        saturation_ratio = float(spec_dict.get("op_saturation_ratio", 0.0) or 0.0)
        alive_ratio = float(spec_dict.get("op_alive_ratio", 0.0) or 0.0)
        return float(2.0 * saturation_ratio + alive_ratio)

    def dc_feasibility_reward(self, spec_dict, strategy="ac_gain"):
        if strategy == "ac_gain":
            return self.ac_gain_reward(spec_dict)
        if strategy == "op_domain":
            return self.op_domain_reward(spec_dict)
        if strategy == "op_ac_domain":
            return self.op_domain_reward(spec_dict) + 0.25 * self.ac_gain_reward(spec_dict)
        raise ValueError(f"Unsupported low-fidelity strategy: {strategy}")

    def evaluate_low_fidelity(self, action, strategy="ac_gain"):
        self.param_values = self.action_refine(action)
        analysis_mode = "op" if strategy == "op_domain" else "op_ac"
        self.real_specs = self.simulate(self.param_values, analysis_mode=analysis_mode)
        reward = self.dc_feasibility_reward(self.real_specs, strategy=strategy)
        return {
            "action": np.asarray(action, dtype=np.float32).copy(),
            "params": dict(self.param_values),
            "specs": dict(self.real_specs),
            "reward": reward,
            "strategy": strategy,
            "netlist_path": getattr(self.simulation_engine, "netlist_path", None),
        }

    def normalize_specs(self, spec_dict):
        norm_dict = {}
        for key, value in spec_dict.items():
            if isinstance(value, (dict, list, np.ndarray)):
                print(f"Normalization Warning: Spec '{key}' is a complex type ({type(value)}). Normalization may not be meaningful.")
                continue
            if value < 0:
                print(f"Normalization Warning: Spec '{key}' has a negative value ({value}). Normalization may not be meaningful.")
            goal = self.dict_targets[key]
            # print("CE: value",value)
            if not np.isfinite(value) or not np.isfinite(goal):
                norm_dict[key] = 0.0# maybe we can treat it better like larger than goal set it inf 1 and --inf -1 
            else:
                k = value + goal if (value + goal) != 0 else 1e-9
                norm_dict[key] = (value - goal) / k
        return norm_dict


    def evaluate(self, action):
        self.param_values = self.action_refine(action)
        # path_id_two_stage = {0: '.\\no_backup\\output_files\\ac_TwoStage.csv', 3: '.\\no_backup\\output_files\\noise_TwoStage.csv', 4: '.\\no_backup\\output_files\\tran_TwoStage.csv', 6: '.\\no_backup\\output_files\\ac_TwoStage.csv', 21: '.\\no_backup\\output_files\\ac_TwoStage.csv', 22: '.\\no_backup\\output_files\\dc_TwoStage.csv'}
        #96
        # path_id = {18: './genai_agent/output/96/ac_dm.csv', 17: './genai_agent/output/96/ac_cm.csv', 0: './genai_agent/output/96/ac_gain.csv', 1: './genai_agent/output/96/ac_gain.csv', 16: './genai_agent/output/96/ac_gain.csv', 6: './genai_agent/output/96/ac_gain.csv', 3: './genai_agent/output/96/noise.csv', 4: './genai_agent/output/96/tran_sr.csv', 10: './genai_agent/output/96/dc_sweep.csv', 11: './genai_agent/output/96/dc_sweep.csv'}

        self.real_specs = self.simulate(self.param_values)
        self.cur_norm_specs = self.normalize_specs(self.real_specs)

    def _build_observation(self, norm_specs):
        """Build a fixed-length observation vector in the YAML target order."""
        obs_values = []
        for key in self.dict_targets.keys():
            value = norm_specs.get(key, -2.0)  # Use -2.0 as a default for missing specs
            if value == -2.0:
                print(f"Warning: Spec '{key}' is missing in normalized specs; using default value -2.0.")
                raise ValueError("key missing in normalized specs")
            if isinstance(value, (list, tuple, np.ndarray)):
                obs_values.extend(np.ravel(np.asarray(value, dtype=np.float32)))
            else:
                obs_values.append(float(value))

        observation = np.asarray(obs_values, dtype=np.float32)
        if observation.size < self.obs_dim:
            observation = np.pad(observation, (0, self.obs_dim - observation.size), constant_values=0.0)
        elif observation.size > self.obs_dim:
            observation = observation[: self.obs_dim]

        return np.nan_to_num(observation, nan=0.0, posinf=1e6, neginf=-1e6)

    def reset(self, *, seed=None, options=None):
        self.episode_steps = 0
        action = np.random.uniform(-1, 1, [self.n_actions])
        self.evaluate(action)
        self.score = 0.0
        
        observation = self._build_observation(self.cur_norm_specs)
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
        observation, reward, hard_satisfied = self.evaluate_full_candidate(action, source="policy")

        self.reward_history.append(reward)
        self.score += reward


        if hard_satisfied:
            plot_running_maximum(self.reward_history, self.run_id)

        self.env_steps += 1
        self.episode_steps += 1

        done = self.episode_steps >= self.max_steps_per_episode

        if self.env_steps % 10 == 0:
            self.score_history.append(self.score)
            plotLearning(self.score_history, self.run_id)
            self.score = 0.0

        info = {'goal_reached': hard_satisfied}
        return observation, reward, done, info

    def evaluate_full_candidate(self, action, source="policy"):
        """Evaluate and persist one full-spec candidate without advancing an RL episode."""
        self.evaluate(action)
        reward, hard_satisfied = self.reward_computation(self.cur_norm_specs)
        if source != "policy":
            self.seed_full_simulations += 1
        self._record_candidate(action, reward, hard_satisfied, source=source)
        self._save_best_candidate(reward, hard_satisfied, source=source)
        observation = self._build_observation(self.cur_norm_specs)

        if hard_satisfied:
            if self.first_success_full_simulations is None:
                self.first_success_full_simulations = self.full_simulations
                self.time_to_first_solution_seconds = self._elapsed_run_seconds()
            self._record_strict_solution(reward, source=source)

        return observation, reward, hard_satisfied

    def _record_strict_solution(self, reward, source="policy"):
        simulation_index = int(self.full_simulations)
        csv_name = file_utils.save_solutions_csv(
            self.run_id,
            simulation_index,
            self.param_values,
            self.real_specs,
            reward,
        )
        solutions2pareto(csv_name, self.run_id, True)
        try:
            netlist_path = getattr(self.simulation_engine, "netlist_path", None)
            if netlist_path and os.path.isfile(netlist_path):
                target_path = os.path.join(
                    self.all_rl_cir_dir,
                    f"pareto_sim_{simulation_index}_{source}.cir",
                )
                shutil.copy(netlist_path, target_path)
                print(f"[CircuitEnv] Saved Pareto netlist to {target_path}")
            else:
                print("[CircuitEnv] Warning: No valid netlist found to copy.")
        except Exception as exc:
            print(f"[CircuitEnv] Failed to copy Pareto netlist: {exc}")

    def _elapsed_run_seconds(self):
        return max(0.0, float(time.time() - self.run_start_time))

    def _record_candidate(self, action, reward, hard_satisfied, source="policy"):
        """Keep passive full-spec trace data for category-level transfer analysis."""
        reward_value = float(np.asarray(reward).reshape(-1)[0])
        record = {
            "step": int(self.env_steps),
            "full_simulation": int(self.full_simulations),
            "source": str(source),
            "action": np.asarray(action, dtype=np.float32).copy(),
            "params": dict(getattr(self, "param_values", {}) or {}),
            "metrics": dict(getattr(self, "real_specs", {}) or {}),
            "normalized_metrics": dict(getattr(self, "cur_norm_specs", {}) or {}),
            "reward": reward_value if np.isfinite(reward_value) else None,
            "strict_pass": bool(hard_satisfied),
        }
        self.candidate_history.append(record)

    @staticmethod
    def _to_serializable(value):
        """Convert NumPy-backed candidate data to JSON-compatible values."""
        if isinstance(value, dict):
            return {str(key): CircuitEnv._to_serializable(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [CircuitEnv._to_serializable(item) for item in value]
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
        return value

    def _save_best_candidate(self, reward, hard_satisfied, source="policy"):
        """Persist a new highest-reward candidate before temporary-file cleanup."""
        reward_value = float(np.asarray(reward).reshape(-1)[0])
        if not np.isfinite(reward_value) or reward_value <= self.best_reward:
            return False

        source_path = getattr(self.simulation_engine, "netlist_path", None)
        if not source_path or not os.path.isfile(source_path):
            print(f"[CircuitEnv] Cannot save best candidate; netlist is missing: {source_path}")
            return False

        target_path = self.best_netlist_target_path 
        

        try:
            shutil.copy2(source_path, target_path)
        except OSError as exc:
            print(f"[CircuitEnv] Failed to save best candidate netlist: {exc}")
            return False

        self.best_reward = reward_value
        self.best_params = dict(self.param_values)
        self.best_specs = dict(self.real_specs)
        self.best_step = self.env_steps
        self.best_hard_satisfied = bool(hard_satisfied)
        self.best_netlist_path = os.path.abspath(target_path)
        self.best_source = str(source)
        self.time_to_best_solution_seconds = self._elapsed_run_seconds()

        metadata = {
            "circuit_name": self.circuit_name,
            "simulation_step": self.best_step,
            "full_simulation": int(self.full_simulations),
            "source": self.best_source,
            "time_to_best_solution_seconds": self.time_to_best_solution_seconds,
            "reward": self.best_reward,
            "constraints_met": self.best_hard_satisfied,
            "circuit_params": self.best_params,
            "specs": self.best_specs,
            "netlist_path": self.best_netlist_path,
        }
        metadata_path = self.best_metadata_path
        temp_metadata_path = metadata_path + ".tmp"
        try:
            with open(temp_metadata_path, "w", encoding="utf-8") as metadata_file:
                json.dump(self._to_serializable(metadata), metadata_file, indent=2, allow_nan=False)
            os.replace(temp_metadata_path, metadata_path)
        except (OSError, TypeError, ValueError) as exc:
            print(f"[CircuitEnv] Best netlist saved, but metadata save failed: {exc}")

        print(
            f"[CircuitEnv] Saved new best candidate at step {self.best_step} "
            f"with reward {self.best_reward:.6g}: {self.best_netlist_path}"
        )
        return True


    def reward_computation(self, norm_specs):
        
        reward = 0.0
        rH = 0.0
        hard_satisfied = False
        # this part is hard
        for key in self.hard_constraints:
            val = norm_specs.get(key, 0.0)
            target = self.dict_targets.get(key, 0.0)
            if key in self.list_min_targets : 
                ry = -max(val, 0.0)
                rH += ry
            else:
                ry = min(val, 0.0)
                rH += ry
            # print(f"{key}: {val}")
            # print("CE:", rH)
        # this part is soft
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
